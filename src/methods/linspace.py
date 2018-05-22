#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BufferedIOBase

import logging
import typing
import iofilter


class Linspace(iofilter.IOFilter[iofilter._T]):
    """Read evenly spaced bytes from the file.

    The space is defined by the parameter step, which is equals to the
    difference between the index of the current byte and the index of the last
    byte in the source bytes sequence.

    """

    PARAM_STEP = 'step'

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
    logger = logging.getLogger(__name__)

    def read(self, size: int) -> bytes:
        super().read(size)

        res = bytearray()
        buf = bytearray()

        step = self.kwargs[self.PARAM_STEP]
        left = (size - 1) * step + 1
        while left > 0:
            bytes_obj = self.stream.read(left)
            left -= len(bytes_obj)
            if len(bytes_obj) < left:
                self.stream.seek(0)

            if not res and not left:
                return bytes_obj[::step]

            buf.extend(bytes_obj)

            tmp = buf[::step]
            if left:
                tmp = tmp[:-1]
                end = len(tmp) * step
                if end:
                    buf = buf[end:]

            if tmp:
                res.extend(tmp)

        return bytes(res)
