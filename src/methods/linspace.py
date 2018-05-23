#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BufferedIOBase
from socket import socket

import logging
import typing
import iofilter


class Linspace(iofilter.IOFilter[iofilter._T]):
    """Read evenly spaced bytes from the underlying stream.

    The space is defined by the parameter step, which is equals to the
    difference between the index of the current byte and the index of the last
    byte in the source bytes sequence.

    """

    logger = logging.getLogger(__name__)

    PARAM_STEP = 'step'

    def get_bufarray_size(self, bufsize: int) -> int:
        return bufsize * self.kwargs[self.PARAM_STEP]

    @classmethod
    def _get_method_params(cls: typing.Type['Linspace']) -> typing.Dict[
            str,
            typing.Callable[[str], iofilter._MethodParam]]:
        return {cls.PARAM_STEP: cls.convert}

    @classmethod
    def convert(
            cls: typing.Type['Linspace'],
            string: str) -> int:
        res = int(string)
        if res < 1:
            err = ValueError("parameter '%s' must be >= 1" % cls.PARAM_STEP)
            cls._log_and_exit(err)
        return res


class LinspaceIO(Linspace[BufferedIOBase]):

    def read(self, size: int) -> bytes:
        super().read(size)

        step = self.kwargs[self.PARAM_STEP]
        view = memoryview(self._buffer)
        start = 0
        end = size * step

        while end > start:
            nbytes = self._stream.readinto(view[start:end])

            if nbytes < end - start:
                self._stream.seek(0)

            start += nbytes

        self._incr_count(end)
        return view[:end][::step].tobytes()


class LinspaceSocket(Linspace[socket]):

    def read(self, size: int) -> bytes:
        super().read(size)

        step = self.kwargs[self.PARAM_STEP]
        view = memoryview(self._buffer)
        start = 0
        left = size * step

        while left > 0:
            nbytes = self._stream.recv_into(view[start:], left)

            if not nbytes:
                break

            start += nbytes
            left -= nbytes

        self._incr_count(start)
        return view[:start][::step].tobytes()
