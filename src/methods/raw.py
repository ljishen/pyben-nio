#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The use of relative imports in Python 3
# https://stackoverflow.com/a/12173406
from .iofilter import IOFilter

import logging
import typing


class Raw(IOFilter):
    """Read the data without any filtering."""

    logger = logging.getLogger(__name__)

    def read(self, size: int) -> bytes:
        super().read(size)

        while True:
            bytes_obj = self.file_obj.read(size)

            if len(bytes_obj) < size:
                self.file_obj.seek(0)

            if bytes_obj:
                return bytes_obj

    @classmethod
    def _get_method_params(cls: typing.Type['Raw']) -> typing.Dict[
            str, typing.Callable[[str], typing.Union[str, int]]]:
        return {}
