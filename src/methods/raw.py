#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BufferedIOBase
from socket import socket

import logging
import typing
import iofilter


class Raw(iofilter.IOFilter[iofilter._T]):
    """Read and return raw data without any filtering."""

    logger = logging.getLogger(__name__)

    @classmethod
    def _get_method_params(cls: typing.Type['Raw']) -> typing.Dict[
            str,
            typing.Callable[[str], iofilter._MethodParam]]:
        return {}


class RawIO(Raw[BufferedIOBase]):

    def read(self, size: int) -> bytes:
        super().read(size)

        view = memoryview(self._buffer)
        while True:
            nbytes = self._stream.readinto(view[:size])

            if nbytes < size:
                self._stream.seek(0)

            if nbytes:
                self._incr_count(nbytes)
                return self._buffer[:nbytes]


class RawSocket(Raw[socket]):

    def read(self, size: int) -> bytes:
        super().read(size)

        nbytes = self._stream.recv_into(self._buffer, size)
        self._incr_count(nbytes)

        return self._buffer[:nbytes]
