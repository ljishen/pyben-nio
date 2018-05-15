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

    def read(self, size):
        while True:
            bytes_obj = self.file_obj.read(size)

            if len(bytes_obj) < size:
                self.file_obj.seek(0)

            if bytes_obj:
                return bytes_obj

    @classmethod
    def _create(
            cls: typing.Type['Linspace'],
            constr_param_names: typing.List[str],
            file_obj: typing.BinaryIO,
            extra_args_dict: typing.Dict[str, str]) -> 'Linspace':
        if extra_args_dict:
            err = ValueError("Unknow method parameters: %s" % extra_args_dict)
            cls._log_and_exit(err)
        return Linspace(file_obj)

    @staticmethod
    def print_desc():
        print('Module: ' + __name__)
        print('\tExtra constructor parameter is not necessary.')
