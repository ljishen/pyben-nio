#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from importlib import import_module
from pkgutil import walk_packages

import inspect
import logging
import re

import methods


class Util(object):
    """A static method utility for convenient to use."""

    logger = logging.getLogger(__name__)

    _SUPPORT_UNITS = ['b', 'kb', 'mb', 'gb']

    @staticmethod
    def list_methods():
        """List all the method names in the methods folder."""
        return [name for _, name, _ in walk_packages(methods.__path__)
                if name != 'iofilter']

    # pylint: disable=inconsistent-return-statements
    @staticmethod
    def get_classobj_of(method, stream_type):
        """Get the class object according to the method name and stream type.

        Args:
            method (str): The name of the method.
            stream_type (type): The type of the stream object.

        """
        module = import_module('.' + method, methods.__name__)
        classes = inspect.getmembers(module, inspect.isclass)

        for cls_tuple in classes:
            cls_obj = cls_tuple[1]

            # Filter out classes not in the current module
            if cls_obj.__module__ != module.__name__:
                continue

            if inspect.isabstract(cls_obj):
                continue

            if hasattr(cls_obj, '__orig_bases__'):
                # For Python 3.6
                # The original bases are stored as __orig_bases__ in the
                # class namespace
                # https://www.python.org/dev/peps/pep-0560/#mro-entries
                bases = cls_obj.__orig_bases__
            else:
                # For Python 3.5
                bases = cls_obj.__bases__

            base = bases[0]
            if not hasattr(base, '__args__'):
                continue

            if not base.__args__:
                continue

            type_arg = base.__args__[0]
            if issubclass(stream_type, type_arg):
                Util.logger.debug("[method class: %r]", cls_obj)
                return cls_obj

        raise Util.value_err(
            Util.logger,
            "No class object of method {!r} found for stream type {}".format(
                method, stream_type))

    # pylint: disable=inconsistent-return-statements
    @staticmethod
    def human2bytes(size: str) -> int:
        """Convert the human readable size to the size in bytes."""
        if '.' in size:
            raise Util.value_err(
                Util.logger,
                "Can't parse non-integer size {!r}".format(size))

        if '-' in size:
            raise Util.value_err(
                Util.logger,
                "Input size {!r} is not positive".format(size))

        num_s = re.split(r'\D+', size)[0]
        if not num_s:
            raise Util.value_err(
                Util.logger,
                "Invalid input size {!r}".format(size))

        unit = size[len(num_s):].lower()
        num = int(num_s)

        if not unit.endswith('b'):
            unit += 'b'

        for unt in Util._SUPPORT_UNITS:
            if unt == unit:
                return num
            num <<= 10

        raise Util.value_err(
            Util.logger,
            "Invalid input size {!r}".format(size))

    @staticmethod
    def value_err(logger, err_msg):
        """Log the error before returning the err object."""
        logger.error(err_msg)
        return ValueError(err_msg)
