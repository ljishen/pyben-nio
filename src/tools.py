#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys

from tools import randints


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s | %(name)-16s | \
%(levelname)-8s | PID=%(process)d | %(message)s',
        level=logging.DEBUG, stream=sys.stdout)

    randints.run()
