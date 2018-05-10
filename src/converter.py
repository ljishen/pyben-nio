#!/usr/bin/env python3

UNITS = ['b', 'kb', 'mb', 'gb']


def human2bytes(size):
    if '.' in size:
        raise ValueError("Can't parse non-integer bufsize %r" % size)

    num = int(''.join(filter(str.isdigit, size)))
    unit = ''.join(filter(str.isalpha, size)).strip().lower()

    if not unit:
        unit = 'b'

    if not unit.endswith('b'):
        unit += 'b'

    for u in UNITS:
        if u == unit:
            return num
        num <<= 10

    raise ValueError("Invalid bufsize %r" % size)
