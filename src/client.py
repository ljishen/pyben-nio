#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import Namespace
from collections import deque
from datetime import datetime as dt
from multiprocessing import Pool

import logging
import socket

from converter import Converter
from paramparser import ParameterParser
from util import Util


def __populate_start_parser(start_parser):
    start_parser.add_argument(
        '-a', '--addresses', metavar='ADDRS', nargs='+',
        help='The list of host names or IP addresses the servers are running on \
              (separated by space)',
        required=True)
    start_parser.add_argument(
        '-s', '--size', type=str,
        help='The total size of data I/O ([BKMG])',
        required=True)
    start_parser.add_argument(
        '-p', '--port', type=int,
        help='The client connects to the port where the server is listening on \
             (default: 8881)',
        default=8881,
        required=False)
    start_parser.add_argument(
        '-b', '--bind', type=str,
        help='Specify the incoming interface for receiving data, \
              rather than allowing the kernel to set the local address to \
              INADDR_ANY during connect (see ip(7), connect(2))',
        required=False)
    start_parser.add_argument(
        '-l', '--bufsize', metavar='BS', type=str,
        help='The maximum amount of data in bytes to be received at once \
              (default: 4096) ([BKMG])',
        default='4K',
        required=False)

    start_parser.set_multi_value_dest('method')
    start_parser.add_argument(
        '-m', '--method', type=str,
        help='The data filtering method to apply on reading from the socket \
              (default: raw). Use semicolon (;) to separate method parameters',
        choices=Util.list_methods(),
        default='raw',
        required=False)


def __get_args():
    prog_desc = 'Simple network socket client with customized \
workload support.'

    parser, start_parser = ParameterParser.create(description=prog_desc)
    __populate_start_parser(start_parser)

    arg_attrs_ns = parser.get_parsed_start_namespace()

    return Namespace(
        host_addrs=arg_attrs_ns.addresses,
        size=Converter.human2bytes(arg_attrs_ns.size),
        port=arg_attrs_ns.port,
        bind_addr=arg_attrs_ns.bind,
        bufsize=Converter.human2bytes(arg_attrs_ns.bufsize),
        method=parser.split_multi_value_param(arg_attrs_ns.method))


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


def __run(idx, classobj, args_ns, size, mem_limit_bs):
    sock = __setup_socket(
        args_ns.host_addrs[idx], args_ns.port, args_ns.bind_addr)
    iofilter = classobj.create(
        sock, args_ns.bufsize, extra_args=args_ns.method[1:])

    left = size
    byte_mem = deque(maxlen=mem_limit_bs)  # type: typing.Deque[int]

    t_start = dt.now().timestamp()
    try:
        while left > 0:
            num_bys = min(args_ns.bufsize, left)
            bytes_obj = iofilter.read(num_bys)
            if not bytes_obj:
                break

            byte_mem.extend(bytes_obj)
            obj_s = len(bytes_obj)
            left -= obj_s

            if logger.isEnabledFor(logging.DEBUG):
                bytes_summary = bytes(bytes_obj[:50])
                logger.debug("Received %d bytes of data (summary %r%s)",
                             obj_s,
                             bytes_summary,
                             '...' if len(bytes_obj) > len(bytes_summary)
                             else '')
    except ValueError:
        logger.exception(
            "Fail to read data from buffered stream %r", iofilter.get_stream())
        raise
    finally:
        t_end = dt.now().timestamp()
        dur = t_end - t_start
        recvd = size - left
        logger.info("Received %d bytes of data in %s seconds \
(bitrate: %s bit/s)",
                    recvd, dur, recvd * 8 / dur)
        iofilter.get_stream().close()
        logger.info("Socket closed")

    return t_start, t_end, recvd, iofilter.get_count()


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
    args_ns = __get_args()
    logger.info("[bufsize: %d bytes]", args_ns.bufsize)

    num_servs = len(args_ns.host_addrs)

    p_sizes = __allot_size(args_ns.size, num_servs)
    classobj = Util.get_classobj_of(args_ns.method[0], socket.socket)

    mem_limit_bs = Converter.human2bytes('500MB') // num_servs

    with Pool(processes=num_servs) as pool:
        futures = [pool.apply_async(__run,
                                    (idx, classobj, args_ns,
                                     size, mem_limit_bs))
                   for idx, size in enumerate(p_sizes)]
        multi_results = [f.get() for f in futures]

    t_starts, t_ends, recvds, raw_byte_counts = zip(*multi_results)
    total_dur = max(t_ends) - min(t_starts)
    total_recvd = sum(recvds)

    total_raw_bytes = sum(raw_byte_counts)

    # We might not receive anything if the server failed.
    raw_bytes_info = ''
    if total_raw_bytes:
        raw_bytes_info = ' (raw {:d}, {:.3f}%)'.format(
            total_raw_bytes, total_recvd / total_raw_bytes * 100)

    logger.info("[SUMMARY] Total received %d%s bytes of data in %s seconds \
(bitrate: %s bit/s)",
                total_recvd,
                raw_bytes_info,
                total_dur,
                total_recvd * 8 / total_dur)


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s | %(name)-16s | \
%(levelname)-8s | PID=%(process)d | %(message)s',
        level=logging.DEBUG)
    logger = logging.getLogger('client')  # pylint: disable=C0103

    main()
