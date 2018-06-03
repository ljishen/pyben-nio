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

    @staticmethod
    def get_classobj_of(method, stream_type=None):
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

            if stream_type:
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

                type_arg = bases[0].__args__[0]
                if issubclass(stream_type, type_arg):
                    Util.logger.debug("[method class: %r]", cls_obj)
                    return cls_obj

            elif inspect.isabstract(cls_obj):
                Util.logger.debug("[method class: %r]", cls_obj)
                return cls_obj

        Util.log_and_raise(
            Util.logger,
            ValueError(
                "No class object of method %r found for stream type %s" %
                (method, stream_type)))

    @staticmethod
    def human2bytes(size):
        """Convert the human readable size to the size in bytes."""
        if '.' in size:
            Util.log_and_raise(
                Util.logger,
                ValueError("Can't parse non-integer size %r" % size))

        if '-' in size:
            Util.log_and_raise(
                Util.logger,
                ValueError("Input size %r is not positive" % size))

        num_s = re.split(r'\D+', size)[0]
        if not num_s:
            Util.log_and_raise(
                Util.logger,
                ValueError("Invalid input size %r" % size))

        unit = size[len(num_s):].lower()
        num = int(num_s)

        if not unit.endswith('b'):
            unit += 'b'

        for unt in Util._SUPPORT_UNITS:
            if unt == unit:
                return num
            num <<= 10

        Util.log_and_raise(
            Util.logger,
            ValueError("Invalid input size %r" % size))

    @staticmethod
    def log_and_raise(logger, err):
        """Log the error before raise it."""
        logger.error(str(err))
        raise err
