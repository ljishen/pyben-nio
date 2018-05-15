#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser


class ParameterParser(ArgumentParser):
    def set_special_dest(self, special_dest: str):
        self.special_dest = special_dest

    def _check_value(self, action, value):
        try:
            if action.dest == self.special_dest:
                value = value.split()[0]
        except AttributeError:
            pass

        super()._check_value(action, value)
