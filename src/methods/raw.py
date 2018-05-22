#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BufferedIOBase

import logging
import typing
import iofilter


class Raw(iofilter.IOFilter[iofilter._T]):
    """Read and return raw data without any filtering."""

    @classmethod
    def _get_method_params(cls: typing.Type['Raw']) -> typing.Dict[
            str,
            typing.Callable[[str], iofilter._MethodParam]]:
        return {}


class RawIO(Raw[BufferedIOBase]):
    logger = logging.getLogger(__name__)

    def read(self, size: int) -> bytes:
        super().read(size)

        while True:
            bytes_obj = self.stream.read(size)

            if len(bytes_obj) < size:
                self.stream.seek(0)

            if bytes_obj:
                return bytes_obj
