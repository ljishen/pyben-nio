#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The use of relative imports in Python 3
# https://stackoverflow.com/a/12173406
from .iofilter import IOFilter

import logging
import typing


class Linspace(IOFilter):
    """Read the data without any filtering."""

    logger = logging.getLogger(__name__)

    def read(self, size: int=-1) -> bytes:
        while True:
            bytes_obj = self.file_obj.read(size)

            if len(bytes_obj) < size:
                self.file_obj.seek(0)

            if bytes_obj:
                return bytes_obj

    @staticmethod
    def _get_method_params() -> typing.Dict[
            str, typing.Callable[[str], typing.Union[str, int]]]:
        return {'step': int}
