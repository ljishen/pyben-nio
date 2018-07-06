#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from enum import Enum
from datetime import datetime as dt
from inspect import getfullargspec
from io import BufferedIOBase
from multiprocessing import Pool
from socket import socket

import abc
import logging
import typing
import os

import iofilter

from util import Util


# pylint: disable=global-statement
class Match(iofilter.IOFilter[iofilter.T]):
    """Read the bytes that match the function check."""

    logger = logging.getLogger(__name__)

    PARAM_FUNC = 'func'
    PARAM_SIZETYPE = 'sztype'

    @classmethod
    def _get_method_params(cls: typing.Type['Match']) -> typing.List[
            iofilter.MethodParam]:
        return [
            iofilter.MethodParam(
                cls.PARAM_FUNC,
                cls.__convert_func,
                'It defines the function check that whether the read \
                operation should return the byte. This function should only \
                accpet a single argument as an int value of the byte and \
                return an object that subsequently will be used in the bytes \
                filtering based on its truth value. \
                Also see truth value testing in Python 3: \
        https://docs.python.org/3/library/stdtypes.html#truth-value-testing'),
            iofilter.MethodParam(
                cls.PARAM_SIZETYPE,
                cls.__convert_size_type,
                'Control the size parameter whether it is the size of the \
                data filtering result (AFTER) or the size of total data read \
                (BEFORE). Choices: [BEFORE(B), AFTER(A)].',
                'AFTER'
            )
        ]

    class SizeType(Enum):
        """Define the choices of parameter sztype."""

        BEFORE = 1
        AFTER = 2

    @classmethod
    def __convert_size_type(
            cls: typing.Type['Match'],
            string: str) -> 'SizeType':
        if string == 'A' or string == cls.SizeType.AFTER.name:
            return cls.SizeType.AFTER
        elif string == 'B' or string == cls.SizeType.BEFORE.name:
            return cls.SizeType.BEFORE

        raise ValueError(
            "Unknow %r value %s" % (cls.PARAM_SIZETYPE, string))

    @classmethod
    def __convert_func(
            cls: typing.Type['Match'],
            expr: str) -> typing.Callable[[int], object]:
        try:
            func = eval(expr)  # pylint: disable=eval-used
        except Exception:
            cls.logger.exception(
                "Unable to parse function expression: %s", expr)
            raise

        try:
            num_args = len(getfullargspec(func).args)
        except TypeError:
            cls.logger.exception(
                "Fail to inspect parameters of function expresstion: %s", expr)
            raise

        if num_args != 1:
            raise ValueError("Function expresstion %s has more than 1 argument"
                             % expr)

        return func

    def read(self: 'Match', size: int) -> typing.Tuple[bytes, int]:
        """Read data from the underlying stream."""
        super().read(size)

        if self.kwargs[self.PARAM_SIZETYPE] == self.SizeType.BEFORE:
            return self._read_before(size)

        return self._read_after(size)

    @abc.abstractmethod
    def _read_before(self: 'Match', size: int) -> typing.Tuple[bytes, int]:
        pass

    @abc.abstractmethod
    def _read_after(self: 'Match', size: int) -> typing.Tuple[bytes, int]:
        pass


# pylint: disable=invalid-name
expr_func = lambda v: v  # noqa: E731


def _check(byte_arr: bytearray, res: bytearray = None) -> bytearray:
    if res is None:
        res = bytearray()

    for byt in byte_arr:
        if expr_func(byt):
            res.append(byt)

    return res


class MatchIO(Match[BufferedIOBase]):
    """Read the bytes from file that match the function check."""

    PARAM_MINPROCWORKSIZE = 'mpws'

    def __init__(
            self: 'MatchIO',
            stream: BufferedIOBase,
            bufsize: int,
            **kwargs) -> None:
        """Initialize addtional attribute for instance of this class.

        Attributes:
            __first_read (bool): Identify if it is the first time of
                reading through the whole file.

        """
        super().__init__(stream, bufsize, **kwargs)
        self.__first_read = True

        global expr_func  # pylint: disable=invalid-name
        # Make this variable global so all the subprocesses can inherit
        # this variable automatically
        expr_func = kwargs[self.PARAM_FUNC]

        num_procs = int(bufsize / kwargs[self.PARAM_MINPROCWORKSIZE] + 0.5)
        if num_procs < 1:
            num_procs = 1
        else:
            num_usable_cpus = len(os.sched_getaffinity(0))
            if num_procs > num_usable_cpus:
                self.kwargs[self.PARAM_MINPROCWORKSIZE] = \
                    int(bufsize / (num_usable_cpus - 0.5))
                self.logger.warning(
                    "Not enough CPU cores available. Change %r to %d bytes",
                    self.PARAM_MINPROCWORKSIZE,
                    self.kwargs[self.PARAM_MINPROCWORKSIZE])
                num_procs = num_usable_cpus

        self._procs_pool = None
        if num_procs > 1:
            self._procs_pool = Pool(processes=num_procs)
        self.logger.info("Start %d process%s to handle data filtering",
                         num_procs,
                         'es' if num_procs > 1 else '')

        self._resbuf = bytearray()

    @classmethod
    def _get_method_params(cls: typing.Type['MatchIO']) -> typing.List[
            iofilter.MethodParam]:
        method_params = super()._get_method_params()
        method_params.append(
            iofilter.MethodParam(
                cls.PARAM_MINPROCWORKSIZE,
                Util.human2bytes,
                'The minimum number of bytes that handle by each process \
                each time. The number of processes in use depends on the \
                bufsize and this value.',
                '50MB'
            )
        )
        return method_params

    def close(self: 'MatchIO') -> None:
        """Close associated resources."""
        super().close()
        if self._procs_pool:
            self._procs_pool.close()

    def __get_and_update_res(self: 'MatchIO', size: int) -> bytearray:
        if size >= len(self._resbuf):
            ret_res = self._resbuf
            self._resbuf = bytearray()
        else:
            ret_res = self._resbuf[:size]
            self._resbuf = self._resbuf[size:]
        return ret_res

    def __allot_work_sizes(
            self: 'MatchIO', total_size: int) -> typing.List[int]:
        min_proc_worksize = self.kwargs[self.PARAM_MINPROCWORKSIZE]

        least_num_procs = total_size // min_proc_worksize
        work_sizes = [min_proc_worksize] * least_num_procs
        left = total_size - least_num_procs * min_proc_worksize
        if left >= min_proc_worksize / 2 or not least_num_procs:
            work_sizes.append(left)
        else:
            work_sizes[-1] += left

        return work_sizes

    def _read_before(self: 'MatchIO', size: int) -> typing.Tuple[bytes, int]:
        view = self._get_or_create_bufview()

        start = 0
        while start < size:
            nbytes = self._stream.readinto(view[start:size])
            if nbytes < size - start:
                self._stream.seek(0)

            start += nbytes

        self.__do_filter(size)
        return (self.__get_and_update_res(len(self._resbuf)), size)

    def __do_filter(self: 'MatchIO', nbytes: int) -> None:
        self._incr_count(nbytes)
        view = self._get_or_create_bufview()

        t_start = dt.now().timestamp()

        if self._procs_pool is None:
            _check(view[:nbytes], res=self._resbuf)
        else:
            work_sizes = self.__allot_work_sizes(nbytes)
            self.logger.debug("work sizes of processes in bytes: %r",
                              work_sizes)

            prev_offset = 0
            future_results = []
            for wsize in work_sizes:
                next_offset = wsize + prev_offset
                future_results.append(
                    self._procs_pool.apply_async(
                        _check,
                        (bytearray(view[prev_offset:next_offset]),))
                )
                prev_offset = next_offset

            for f_res in future_results:
                self._resbuf.extend(f_res.get())

        if self.logger.isEnabledFor(logging.DEBUG):
            t_dur = dt.now().timestamp() - t_start
            self.logger.debug(
                "Took %s seconds to filter %d bytes of data",
                t_dur,
                nbytes)

    def _read_after(self: 'MatchIO', size: int) -> typing.Tuple[bytes, int]:
        if len(self._resbuf) >= size:
            return (self.__get_and_update_res(size), size)

        view = self._get_or_create_bufview()

        while True:
            nbytes = self._stream.readinto(view[:size])
            if nbytes < size:
                self._stream.seek(0)

            if nbytes:
                self.__do_filter(nbytes)

                if len(self._resbuf) >= size:
                    self.__first_read = False
                    return (self.__get_and_update_res(size), size)

            if (self.__first_read
                    and self._stream.tell() == 0
                    and not self._resbuf):
                raise ValueError(
                    "No matching byte in the buffered stream %r"
                    % self._stream)


class MatchSocket(Match[socket]):
    """Read the bytes from socket that match the function check."""

    def __init__(
            self: 'MatchSocket',
            stream: socket,
            bufsize: int,
            **kwargs) -> None:
        """Initialize addtional attribute for instance of this class.

        Attributes:
            __byteque (typing.Deque[int]): Store the read bytes from
                the underlying stream.

        """
        super().__init__(stream, bufsize, **kwargs)
        self.__byteque = deque()  # type: typing.Deque[int]

    def _read_after(self: 'MatchSocket', size: int) -> typing.Tuple[
            bytes, int]:
        res = bytearray()
        view = self._get_or_create_bufview()
        func = self.kwargs[self.PARAM_FUNC]

        while True:
            if self.__byteque:
                try:
                    while True:
                        byt_val = self.__byteque.popleft()  # type: int
                        if func(byt_val):
                            res.append(byt_val)
                            if len(res) == size:
                                return (res, size)
                except IndexError:
                    pass

            nbytes = self._stream.recv_into(view, size)
            if not nbytes:
                return (res, len(res))

            self._incr_count(nbytes)
            self.__byteque.extend(view[:nbytes])

    def _read_before(self: 'MatchSocket', size: int) -> typing.Tuple[
            bytes, int]:
        res = bytearray()
        view = self._get_or_create_bufview()

        nbytes = self._stream.recv_into(view, size)
        if not nbytes:
            return (res, 0)

        self._incr_count(nbytes)

        func = self.kwargs[self.PARAM_FUNC]
        for byt_val in view[:nbytes]:
            if func(byt_val):
                res.append(byt_val)
        return (res, nbytes)
