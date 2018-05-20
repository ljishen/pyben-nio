#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from importlib import import_module
from pkgutil import walk_packages

import methods


class Util(object):
    """A static method utility for convenient to use."""

    @staticmethod
    def list_methods():
        """List all the method names in the methods folder."""
        return [name for _, name, _ in walk_packages(methods.__path__)
                if name != 'iofilter']

    @staticmethod
    def get_classobj_of(method):
        """Get the class object according to the method name.

        Args:
            method (str): The name of the method.

        """
        return getattr(
            import_module('.' + method, methods.__package__),
            method.capitalize())
