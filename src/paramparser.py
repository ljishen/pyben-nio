#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser

import re


class ParameterParser(ArgumentParser):
    def set_multi_value_dest(self, multi_value_dest: str):
        self.multi_value_dest = multi_value_dest

    def _check_value(self, action, value):
        try:
            if action.dest == self.multi_value_dest:
                value = self.split_multi_value_params(value)[0]
        except AttributeError:
            pass

        super()._check_value(action, value)

    @staticmethod
    def split_multi_value_params(string: str):
        items = re.split(';', string.strip().rstrip(';'))
        return list(map(str.strip, items))
