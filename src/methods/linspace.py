#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The use of relative imports in Python 3
# https://stackoverflow.com/a/12173406
from .iofilter import IOFilter

import logging
import typing


class Linspace(IOFilter):
    """Read evenly spaced bytes from the file."""

    logger = logging.getLogger(__name__)

    def read(self, size: int=-1) -> bytes:
        while True:
            bytes_obj = self.file_obj.read(size)

            if len(bytes_obj) < size:
                self.file_obj.seek(0)

            if bytes_obj:
                return bytes_obj

    @classmethod
    def _get_method_params(
            cls: typing.Type['Linspace']) -> typing.Dict[
            str, typing.Callable[[str], typing.Union[str, int]]]:
        return {'step': cls.convert}

    @classmethod
    def convert(
            cls: typing.Type['IOFilter'],
            step: str) -> int:
        res = int(step)
        if res < 1:
            err = ValueError("parameter 'step' must be >= 1")
            cls._log_and_exit(err)
        return res
