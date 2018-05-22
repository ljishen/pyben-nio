#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from importlib import import_module
from pkgutil import walk_packages

import inspect
import logging
import methods


class Util(object):
    """A static method utility for convenient to use."""

    logger = logging.getLogger(__name__)

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

                type_arg = cls_obj.__bases__[0].__args__[0]
                if issubclass(stream_type, type_arg):
                    Util.logger.debug("[method class: %r]", cls_obj)
                    return cls_obj

            elif inspect.isabstract(cls_obj):
                Util.logger.debug("[method class: %r]", cls_obj)
                return cls_obj

        err = ValueError(
            "No class object of method %r found for stream type %s" %
            (method, stream_type))
        Util.logger.error(str(err))
        raise err
