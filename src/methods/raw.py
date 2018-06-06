#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BufferedIOBase
from socket import socket

import logging
import iofilter


class Raw(iofilter.IOFilter[iofilter.T]):
    """Read and return raw data without any filtering."""

    logger = logging.getLogger(__name__)


class RawIO(Raw[BufferedIOBase]):
    """Read from file and return raw data without any filtering."""

    def read(self, size: int) -> bytes:
        """Read data from the file stream."""
        super().read(size)

        view = self._get_or_create_bufview()
        while True:
            nbytes = self._stream.readinto(view[:size])

            if nbytes < size:
                self._stream.seek(0)

            if nbytes:
                self._incr_count(nbytes)
                return self._buffer[:nbytes]


class RawSocket(Raw[socket]):
    """Read from socket and return raw data without any filtering."""

    def read(self, size: int) -> bytes:
        """Read data from the socket stream."""
        super().read(size)

        nbytes = self._stream.recv_into(self._buffer, size)
        self._incr_count(nbytes)

        return self._buffer[:nbytes]
