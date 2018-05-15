#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re


class Converter(object):
    support_units = ['b', 'kb', 'mb', 'gb']
    logger = logging.getLogger(__name__)

    @classmethod
    def human2bytes(cls, size):
        if '.' in size:
            cls.__log_and_exit(
                ValueError("Can't parse non-integer bufsize %r" % size))

        num_s = re.split(r'\D+', size)[0]
        if not num_s:
            cls.__log_and_exit(ValueError("Invalid bufsize %r" % size))

        unit = size[len(num_s):].lower()
        num = int(num_s)

        if not unit.endswith('b'):
            unit += 'b'

        for unt in cls.support_units:
            if unt == unit:
                return num
            num <<= 10

        cls.__log_and_exit(ValueError("Invalid bufsize %r" % size))

    @classmethod
    def __log_and_exit(cls, err):
        cls.logger.error(str(err))
        raise err
