#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BufferedIOBase
from socket import socket

import logging
import typing
import iofilter


class Linspace(iofilter.IOFilter[iofilter.T]):
    """Read evenly spaced bytes from the underlying stream.

    The space is defined by the parameter step.

    """

    logger = logging.getLogger(__name__)

    PARAM_STEP = 'step'

    def _get_bufarray_size(self, bufsize: int) -> int:
        return bufsize * self.kwargs[self.PARAM_STEP]

    @classmethod
    def _get_method_params(cls: typing.Type['Linspace']) -> typing.List[
            iofilter.MethodParam]:
        return [iofilter.MethodParam(
            cls.PARAM_STEP,
            cls.__convert,
            'The space between the read bytes. It is equals to the difference \
            between the index of the current byte and the index of the last \
            byte in the source byte sequence.')]

    @classmethod
    def __convert(
            cls: typing.Type['Linspace'],
            string: str) -> int:
        res = int(string)
        if res < 1:
            raise ValueError("parameter '%s' must be >= 1" % cls.PARAM_STEP)
        return res


class LinspaceIO(Linspace[BufferedIOBase]):
    """Read evenly spaced bytes from file.

    The space is defined by the parameter step.

    """

    def read(self, size: int) -> typing.Tuple[bytes, int]:
        """Read data from the file stream."""
        super().read(size)

        step = self.kwargs[self.PARAM_STEP]
        view = self._get_or_create_bufview()
        start = 0
        end = size * step

        while end > start:
            nbytes = self._stream.readinto(view[start:end])

            if nbytes < end - start:
                self._stream.seek(0)

            start += nbytes

        self._incr_count(end)
        return (view[:end][::step].tobytes(), size)


class LinspaceSocket(Linspace[socket]):
    """Read evenly spaced bytes from socket.

    The space is defined by the parameter step.

    """

    def read(self, size: int) -> typing.Tuple[bytes, int]:
        """Read data from the socket stream."""
        super().read(size)

        step = self.kwargs[self.PARAM_STEP]
        view = self._get_or_create_bufview()
        start = 0
        left = size * step

        while left > 0:
            nbytes = self._stream.recv_into(view[start:], left)

            if not nbytes:
                break

            start += nbytes
            left -= nbytes

        self._incr_count(start)

        res_bytes = view[:start][::step].tobytes()
        return (res_bytes, len(res_bytes))
