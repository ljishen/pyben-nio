#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser

import re
import sys

from version import MyVersionAction
from util import Util


class ParameterParser(ArgumentParser):

    _SUBPARSER_DEST_NAME = "subparser_dest"

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

        # pylint: disable=missing-super-argument
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

    @classmethod
    def create(cls, *args, **kwargs):
        """Create an instance of the ParameterParser.

        Returns:
            The instance of the ParameterParser as parser and its subparser
            start_parser.

        """
        parser = ParameterParser(*args, **kwargs)
        MyVersionAction.set_prog_desc(kwargs['description'])
        parser.add_argument('-v', '--version', action=MyVersionAction,
                            version='%(prog)s version 1.1')

        subparsers = parser.add_subparsers(
            dest=cls._SUBPARSER_DEST_NAME,
            help='Select either command to show more messages')

        start_parser = subparsers.add_parser(
            cls._START_PARSER_NAME,
            epilog='[BKMG] indicates options that support a \
                    B/K/M/G (b/kb/mb/gb) suffix for \
                    byte, kilobyte, megabyte, or gigabyte')
        start_parser.add_argument(
            '-d', '--debug', action='store_true',
            help='Show debug messages',
            default=False,
            required=False)

        desc_parser = subparsers.add_parser(cls._DESC_PARSER_NAME)
        desc_parser.add_argument(
            '-m', '--method', type=str,
            help='Show description messages for specific data filtering \
                  method',
            choices=Util.list_methods(),
            required=not cls.is_start_in_argv_list())
        desc_parser.add_argument(
            '-d', '--debug', action='store_true',
            help='Show debug messages',
            default=False,
            required=False)

        return parser, start_parser

    @classmethod
    def is_start_in_argv_list(cls):
        """Check if the START_PARSER_NAME in the command line argument list."""
        return cls._START_PARSER_NAME in sys.argv

    def get_parsed_namespace(self):
        """Get the populated namespace after converting argument strings.

        Returns:
            Namespace: The namesapce that encapsulates all argument
                attributes.

            See the description of the return type Namespace:
                https://docs.python.org/3/library/argparse.html#argparse.Namespace

        """
        # pylint: disable=attribute-defined-outside-init
        self.arg_attrs_namespace = self.parse_args()
        return self.arg_attrs_namespace

    def is_desc_parser_invoked(self):
        """Check if the dest of the subparsers is the _DESC_PARSER_NAME.

        Returns:
            bool: None if no parser has been invoked and True/False indicates
                the result.

        """
        if not hasattr(self, 'arg_attrs_namespace'):
            return None

        invoked_subparser = getattr(
            self.arg_attrs_namespace, self._SUBPARSER_DEST_NAME)
        return invoked_subparser == self._DESC_PARSER_NAME
