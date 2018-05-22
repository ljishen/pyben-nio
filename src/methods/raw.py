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

    def get_bufarray_size(self, bufsize: int) -> int:
        return bufsize

    @classmethod
    def _get_method_params(cls: typing.Type['Raw']) -> typing.Dict[
            str,
            typing.Callable[[str], iofilter._MethodParam]]:
        return {}


class RawIO(Raw[BufferedIOBase]):

    def read(self, size: int) -> bytes:
        super().read(size)

        while True:
            nbytes = self.stream.readinto(self.buffer)

            if nbytes < size:
                self.stream.seek(0)

            if nbytes:
                return self.buffer[:nbytes]


class RawSocket(Raw[socket]):

    def read(self, size: int) -> bytes:
        super().read(size)

        nbytes = self.stream.recv_into(self.buffer, size)

        return self.buffer[:nbytes]
