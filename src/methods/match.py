#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from inspect import getfullargspec
from io import BufferedIOBase

import logging
import typing
import iofilter


class Match(iofilter.IOFilter[iofilter._T]):
    """Read the bytes that match the function check.

    The parameter func defines the function check that whether the read
    operation should return the byte. The checking function should only accpet
    a single argument as an int value representing the byte and return an
    object that subsequently will be used in bytes filtering based on its truth
    value.

    Also see truth value testing in Python 3:
    https://docs.python.org/3/library/stdtypes.html#truth-value-testing

    """

    logger = logging.getLogger(__name__)

    PARAM_FUNC = 'func'

    @classmethod
    def _get_method_params(cls: typing.Type['Match']) -> typing.Dict[
            str,
            typing.Callable[[str], iofilter._MethodParam]]:
        return {cls.PARAM_FUNC: cls.convert}

    @classmethod
    def convert(
            cls: typing.Type['Match'],
            expr: str) -> typing.Callable[[int], object]:
        try:
            func = eval(expr)
        except Exception:
            cls.logger.exception(
                "Unable to parse function expression: %s" % expr)
            raise

        try:
            num_args = len(getfullargspec(func).args)
        except TypeError:
            cls.logger.exception(
                "Fail to inspect parameters of function expresstion: %s"
                % expr)
            raise

        if num_args != 1:
            cls._log_and_exit(
                ValueError("Function expresstion %s has more than 1 argument"
                           % expr))

        return func


class MatchIO(Match[BufferedIOBase]):

    def __init__(
            self,
            stream: BufferedIOBase,
            **kwargs) -> None:
        super().__init__(stream, **kwargs)
        self.bytebuf = deque()  # type: typing.Deque[int]
        self.first_read = True

    def read(self, size: int) -> bytes:
        super().read(size)

        res = bytearray()
        func = self.kwargs[self.PARAM_FUNC]

        while True:
            if self.bytebuf:
                try:
                    while True:
                        byt_val = self.bytebuf.popleft()
                        if func(byt_val):
                            res.append(byt_val)
                            if len(res) == size:
                                self.first_read = False
                                return res
                except IndexError:
                    self.__check_no_match(res)
                    pass

            bytes_obj = self._stream.read(size)
            if len(bytes_obj) < size:
                self._stream.seek(0)

            if bytes_obj:
                self.bytebuf.extend(bytes_obj)
            else:
                self.__check_no_match(res)

    def __check_no_match(self: 'MatchIO', bytarr: bytearray) -> None:
        if (self.first_read
                and self._stream.tell() == 0
                and not bytarr):
            raise ValueError(
                "No matching byte in the buffered stream %r"
                % self._stream)
