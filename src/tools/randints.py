#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime as dt
from multiprocessing import Pool
from random import randint

import argparse
import importlib.util
import logging
import os
import subprocess

from util import Util

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def __get_args():
    parser = argparse.ArgumentParser(
        description='Efficient random digits in parallel generator.')
    parser.add_argument(
        'count', type=str,
        help='Output count of random digits')
    parser.add_argument(
        '-f', '--filename', type=str,
        help='Write result to FILE (default: data_file)',
        default='data_file')
    parser.add_argument(
        '-p', '--processes', type=int,
        help='Number of processes to generate random digits in parallel \
              instead of spawning one process per available CPU core',
        default=len(os.sched_getaffinity(0)))
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help='Show debug messages',
        default=False)

    args = parser.parse_args()

    if not args.debug:
        logging.disable(logging.DEBUG)

    count = Util.human2bytes(args.count)
    filename = args.filename
    num_procs = args.processes

    return count, filename, num_procs


def __randint(exclusive_n):
    return randint(0, exclusive_n - 1)


def __do_run(filename, count):
    spec = importlib.util.find_spec('secrets')
    if spec is None:
        # Fallback to the insecure approach
        rand_module = importlib.import_module('random')
        randbelow = __randint
    else:
        rand_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rand_module)
        randbelow = rand_module.randbelow

    part_filename = filename + '.' + str(os.getpid())
    logger.debug("Writing %d bytes to %r", count, part_filename)

    with open(part_filename, 'w') as fobj:
        for _ in range(count):
            fobj.write(str(randbelow(10)))
    return part_filename


def __split(count, num):
    i_count = count // num
    left = count - i_count * num

    p_count = []
    for i in range(num):
        p_count.append(i_count)
        if i < left:
            p_count[i] += 1

    return p_count


def run():
    """Entrypoint function for calling general tool."""
    count, filename, num_procs = __get_args()
    logger.info("[result file: %r]", filename)

    spec = importlib.util.find_spec('secrets')
    if spec is None:
        logger.info("Use random method 'random.randint(a, b)'")
    else:
        logger.info("Use random method 'secrets.randbelow(n)'")

    if os.path.exists(filename):
        logger.warning("Delete obsolete %r", filename)
        subprocess.run(["rm", "-rf", filename])

    subprocess.run("rm -rf " + filename + ".*", shell=True)

    with Pool(processes=num_procs) as pool:
        t_start = dt.now().timestamp()

        multiple_results = \
            [pool.apply_async(__do_run, (filename, p_count))
             for p_count in __split(count, num_procs)]

        for res in multiple_results:
            part_filename = res.get()
            logger.debug("Merging %r to %r", part_filename, filename)

            if os.path.isfile(filename):
                try:
                    subprocess.run("cat " + part_filename + " >> " + filename +
                                   " && rm " + part_filename,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True, check=True)
                except subprocess.CalledProcessError:
                    logger.exception("Fail to merge %r", part_filename)
                    raise
            else:
                os.replace(part_filename, filename)

        t_end = dt.now().timestamp()
        logger.info("Total time consumption: %s seconds", (t_end - t_start))
