#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys


class MyVersionAction(argparse._VersionAction):
    """Customized action class for version print."""

    prog_desc = ''

    @classmethod
    def set_prog_desc(cls, prog_desc):
        """Set the program description for this version action class."""
        cls.prog_desc = prog_desc

    def __call__(self, parser, namespace, values, option_string=None):
        version = self.version
        if version is None:
            version = parser.version
        formatter = parser._get_formatter()
        formatter.add_text(version)
        parser._print_message(
            self.prog_desc +
            "\nOpen Source License: MIT\n\n" +
            formatter.format_help(), sys.stdout)
        parser.exit()
