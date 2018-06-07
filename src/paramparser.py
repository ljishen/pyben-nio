#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser

import logging
import re
import sys

from version import MyVersionAction
from util import Util


class ParameterParser(ArgumentParser):
    """Subclass that helps to setup common arguments."""

    _START_PARSER_NAME = 'start'
    _DESC_PARSER_NAME = 'desc'

    def set_multi_value_dest(self, multi_value_dest):
        """Set to remember the dest of the multi-value parameter.

        Args:
            multi_value_dest (str): The multi-value desc in string.

        """
        # pylint: disable=attribute-defined-outside-init
        self.multi_value_dest = multi_value_dest

    def _check_value(self, action, value):
        try:
            if action.dest == self.multi_value_dest:
                value = self.split_multi_value_param(value)[0]
        except AttributeError:
            pass

        super()._check_value(action, value)

    @staticmethod
    def split_multi_value_param(string):
        """Split the value of multi-value parameter.

        Args:
            string (str): The value of the parameter.

        Returns:
            typing.List[str]: A list of strings each with both leading and
                trailing whitespace stripped.

        """
        items = re.split(';', string.strip().rstrip(';'))
        return [i.strip() for i in items]

    def prepare(self, stream_type):
        """Prepare and config the basic common settings.

        Returns:
            The subparser start_parser to be populated specifically later.

        """
        MyVersionAction.set_prog_desc(self.description)
        self.add_argument('-v', '--version', action=MyVersionAction,
                          version='%(prog)s version 0.3')

        subparsers = self.add_subparsers(
            help='Select either command to show more messages')

        start_parser = subparsers.add_parser(
            self._START_PARSER_NAME,
            epilog='[BKMG] indicates options that support a \
                    B/K/M/G (b/kb/mb/gb) suffix for \
                    byte, kilobyte, megabyte, or gigabyte')
        start_parser.add_argument(
            '-d', '--debug', action='store_true',
            help='Show debug messages',
            default=False,
            required=False)

        desc_parser = subparsers.add_parser(self._DESC_PARSER_NAME)
        desc_parser.add_argument(
            '-m', '--method', type=str,
            help='Show description messages for specific data filtering \
                  method',
            choices=Util.list_methods(),
            required=not self.is_start_in_argv_list())
        desc_parser.add_argument(
            '-d', '--debug', action='store_true',
            help='Show debug messages',
            default=False,
            required=False)
        desc_parser.set_defaults(
            func=lambda arg_attrs_ns: Util.get_classobj_of(
                arg_attrs_ns.method, stream_type).print_desc())

        return start_parser

    @classmethod
    def is_start_in_argv_list(cls):
        """Check if the START_PARSER_NAME in the command line argument list."""
        return cls._START_PARSER_NAME in sys.argv

    def parse_args(self, args=None, namespace=None):
        """Convert arguments as attributes of the namespace.

        Note that this function internally calls the associated function of
        each subparser set by set_defaults().

        Returns:
            Namespace: The populated namespace.

            See the description of the return type Namespace:
                https://docs.python.org/3/library/argparse.html#argparse.Namespace

        """
        arg_attrs_ns = super().parse_args(args, namespace)

        if not arg_attrs_ns.debug:
            logging.disable(logging.DEBUG)

        arg_attrs_ns.func(arg_attrs_ns)

        return arg_attrs_ns
