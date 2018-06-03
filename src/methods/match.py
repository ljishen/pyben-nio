#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from inspect import getfullargspec
from io import BufferedIOBase
from socket import socket

import logging
import typing
import iofilter


class Match(iofilter.IOFilter[iofilter.T]):
    """Read the bytes that match the function check."""

    logger = logging.getLogger(__name__)

    PARAM_FUNC = 'func'
    PARAM_PROCS = 'procs'

    def __init__(
            self: 'Match',
            stream: iofilter.T,
            bufsize: int,
            **kwargs) -> None:
        """Initialize base attributes for all subclasses."""
        super().__init__(stream, bufsize, **kwargs)
        self._byteque = deque()  # type: typing.Deque[int]

    @classmethod
    def _get_method_params(cls: typing.Type['Match']) -> typing.List[
            iofilter.MethodParam]:
        return [
            iofilter.MethodParam(
                cls.PARAM_FUNC,
                cls.__convert,
                'It defines the function check that whether the read \
                operation should return the byte. This function should only \
                accpet a single argument as an int value of the byte and \
                return an object that subsequently will be used in the bytes \
                filtering based on its truth value. \
                Also see truth value testing in Python 3: \
        https://docs.python.org/3/library/stdtypes.html#truth-value-testing'),
            iofilter.MethodParam(
                cls.PARAM_PROCS,
                int,
                'The number of processes to handle the data filtering in \
                parallel.',
                1)
        ]

    @classmethod
    def __convert(
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


class MatchIO(Match[BufferedIOBase]):
    """A subclass to handle reading data from file."""

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

    def read(self, size: int) -> bytes:
        """Read data from the file stream."""
        super().read(size)

        res = bytearray()
        view = self._get_or_create_bufview()
        func = self.kwargs[self.PARAM_FUNC]

        while True:
            if self._byteque:
                try:
                    while True:
                        byt_val = self._byteque.popleft()  # type: int
                        if func(byt_val):
                            res.append(byt_val)
                            if len(res) == size:
                                self.__first_read = False
                                return res
                except IndexError:
                    self.__check_no_match(res)

            nbytes = self._stream.readinto(view[:size])
            if nbytes < size:
                self._stream.seek(0)

            if nbytes:
                self._incr_count(nbytes)
                self._byteque.extend(view[:nbytes])
            else:
                self.__check_no_match(res)

    def __check_no_match(self: 'MatchIO', bytarr: bytearray) -> None:
        if (self.__first_read
                and self._stream.tell() == 0
                and not bytarr):
            raise ValueError(
                "No matching byte in the buffered stream %r"
                % self._stream)


class MatchSocket(Match[socket]):
    """A subclass to handle reading data from socket."""

    def read(self, size: int) -> bytes:
        """Read data from the socket stream."""
        super().read(size)

        res = bytearray()
        view = self._get_or_create_bufview()
        func = self.kwargs[self.PARAM_FUNC]

        while True:
            if self._byteque:
                try:
                    while True:
                        byt_val = self._byteque.popleft()  # type: int
                        if func(byt_val):
                            res.append(byt_val)
                            if len(res) == size:
                                return res
                except IndexError:
                    pass

            nbytes = self._stream.recv_into(view, size)
            if not nbytes:
                return res

            self._incr_count(nbytes)
            self._byteque.extend(view[:nbytes])
