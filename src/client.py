#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime as dt
from multiprocessing import Pool

import argparse
import logging
import socket

from converter import Converter


def __get_args():
    parser = argparse.ArgumentParser(
        description='Simple network socket client.',
        epilog='[BKMG] indicates options that support a \
                B/K/M/G (b/kb/mb/gb) suffix for \
                byte, kilobyte, megabyte, or gigabyte')

    parser.add_argument(
        '-a', '--addresses', metavar='ADDRS', nargs='+',
        help='The list of host names or IP addresses the servers are running on \
              (separated by space)',
        required=True)
    parser.add_argument(
        '-s', '--size', type=str,
        help='The total size of raw data I/O ([BKMG])',
        required=True)
    parser.add_argument(
        '-p', '--port', type=int,
        help='The client connects to the port where the server is listening on \
             (default: 8881)',
        default=8881,
        required=False)
    parser.add_argument(
        '-b', '--bind', type=str,
        help='Specify the incoming interface for receiving data, \
              rather than allowing the kernel to set the local address to \
              INADDR_ANY during connect (see ip(7), connect(2))',
        required=False)
    parser.add_argument(
        '-l', '--bufsize', metavar='BS', type=str,
        help='The maximum amount of data in bytes to be received at once \
              (default: 4096) ([BKMG])',
        default='4K',
        required=False)
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help='Show debug messages',
        default=False,
        required=False)

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    host_addrs = args.addresses
    size = Converter.human2bytes(args.size)
    port = args.port
    bind_addr = args.bind
    bufsize = Converter.human2bytes(args.bufsize)

    return host_addrs, size, port, bind_addr, bufsize


def __setup_socket(addr, port, bind_addr):
    # Create TCP socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        logger.exception("Could not create socket")
        raise

    logger.info("Connecting to server %s on port %d", addr, port)

    if bind_addr:
        # Bind the interface for data receiving
        try:
            # See the "The port 0 trick"
            # (https://www.dnorth.net/2012/03/17/the-port-0-trick/)
            # and "Bind before connect"
            # (https://idea.popcount.org/2014-04-03-bind-before-connect/)
            #
            # We might not need to set the socket flag SO_REUSEADDR since
            # the server side also ready does so.
            sock.bind((bind_addr, 0))
        except socket.error:
            logger.exception(
                "Unable to bind on the local address %s", bind_addr)
            sock.close()
            sock = None
            raise

    # Connect to server
    try:
        sock.connect((addr, port))
    except socket.error:
        logger.exception("Could not connect to the server %s", addr)
        sock.close()
        sock = None
        raise

    logger.info("Connection established. Receiving data ...")
    return sock


def __run(addr, size, port, bind_addr, bufsize, mem_limit_bs):
    sock = __setup_socket(addr, port, bind_addr)

    left = size
    objs_size = 0
    obj_pool = []

    t_start = dt.now().timestamp()
    try:
        while left > 0:
            bys = min(bufsize, left)
            bytes_obj = sock.recv(bys)
            if not bytes_obj:
                break

            obj_s = len(bytes_obj)
            logger.debug("Received %d bytes of data", obj_s)
            obj_pool.append(bytes_obj)
            left -= obj_s
            objs_size += obj_s
            if objs_size > mem_limit_bs:
                del obj_pool[:(len(obj_pool) // 2)]
                objs_size //= 2
    finally:
        t_end = dt.now().timestamp()
        dur = t_end - t_start
        recvd = size - left
        logger.info("Received %d bytes of data in %s seconds \
(bitrate: %s bit/s)",
                    recvd, dur, recvd * 8 / dur)
        sock.close()
        logger.info("Socket closed")

    return t_start, t_end, recvd


def __allot_size(size, num):
    i_size = size // num
    left = size - i_size * num

    p_sizes = []
    for i in range(num):
        p_sizes.append(i_size)
        if i < left:
            p_sizes[i] += 1

    return p_sizes


def main():
    host_addrs, size, port, bind_addr, bufsize = __get_args()
    logger.info("[bufsize: %d bytes]", bufsize)

    num_servs = len(host_addrs)

    p_sizes = __allot_size(size, num_servs)
    mem_limit_bs = Converter.human2bytes('500MB') // num_servs

    with Pool(processes=num_servs) as pool:
        futures = [pool.apply_async(__run,
                                    (addr, p_sizes[idx], port, bind_addr,
                                     bufsize, mem_limit_bs))
                   for idx, addr in enumerate(host_addrs)]
        multi_results = [f.get() for f in futures]

    t_starts, t_ends, recvds = zip(*multi_results)
    total_dur = max(t_ends) - min(t_starts)
    total_recvd = sum(recvds)
    logger.info("[SUMMARY] Total received %d bytes of data in %s seconds \
(bitrate: %s bit/s)",
                total_recvd, total_dur, total_recvd * 8 / total_dur)


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s | %(name)s | \
%(levelname)-8s | PID=%(process)d | %(message)s',
        level=logging.INFO)
    logger = logging.getLogger('client')  # pylint: disable=C0103

    main()
