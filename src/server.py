#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import Namespace
from datetime import datetime as dt
from io import BufferedIOBase

import logging
import os
import socket
import tempfile

from paramparser import ParameterParser
from util import Util


def __populate_start_parser(start_parser):
    start_parser.add_argument(
        '-b', '--bind', type=str,
        help='Bind to host, one of this machine\'s outbound interface',
        required=start_parser.is_start_in_argv_list())
    start_parser.add_argument(
        '-s', '--size', type=str,
        help='The total size of data I/O ([BKMG])',
        required=start_parser.is_start_in_argv_list())
    start_parser.add_argument(
        '-p', '--port', type=int,
        help='The port for the server to listen on (default: 8881)',
        default=8881)
    start_parser.add_argument(
        '-f', '--filename', metavar='FN', type=str,
        help='Read from this file and write to the network, \
              instead of generating a temporary file with random data')
    start_parser.add_argument(
        '-l', '--bufsize', metavar='BS', type=str,
        help='The maximum amount of data in bytes to be sent at once \
              (default: 4K) ([BKMG])',
        default='4K')

    # Since socket.sendfile() performs the data reading and sending within
    # the kernel space, there is no user space function can inject into
    # during this process. Therefore the zerocopy option is conflicting with
    # the method option.
    group = start_parser.add_mutually_exclusive_group()
    start_parser.set_multi_value_dest('method')
    group.add_argument(
        '-m', '--method', type=str,
        help='The data filtering method to apply on reading from the file \
              (default: raw). Use semicolon (;) to separate method parameters',
        choices=Util.list_methods(),
        default='raw')
    group.add_argument(
        '-z', '--zerocopy', action='store_true',
        help='Use "socket.sendfile()" instead of "socket.send()".')

    start_parser.set_defaults(func=__handle_start)


def __handle_start(arg_attrs_ns):
    args_ns = Namespace(
        bind_addr=arg_attrs_ns.bind,
        size=Util.human2bytes(arg_attrs_ns.size),
        port=arg_attrs_ns.port,
        filename=arg_attrs_ns.filename,
        bufsize=Util.human2bytes(arg_attrs_ns.bufsize),
        method=ParameterParser.split_multi_value_param(arg_attrs_ns.method),
        zerocopy=arg_attrs_ns.zerocopy)

    __do_start(args_ns)


def __validate_file(filename, size):
    if filename:
        try:
            return open(filename, "rb")
        except OSError:
            logger.exception("Can't open %s", filename)
            raise

    file_obj = tempfile.TemporaryFile('w+b')
    logger.info("Generating temporary file of size %d bytes ...", size)
    try:
        file_obj.write(os.urandom(size))
        file_obj.seek(0)
    except OSError:
        logger.exception("Can't write to temporary file")
        file_obj.close()
        raise

    return file_obj


def __setup_socket(bind_addr, port):
    # Create TCP socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        logger.exception("Could not create socket")
        raise

    # Bind to listening port
    try:
        # The SO_REUSEADDR flag tells the kernel to reuse a local socket
        # in TIME_WAIT state, without waiting for its natural timeout to
        # expire.
        # See https://docs.python.org/3.6/library/socket.html#example
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind((bind_addr, port))
    except socket.error:
        logger.exception("Unable to bind on port %d", port)
        sock.close()
        sock = None
        raise

    # Listen
    try:
        sock.listen(1)
    except socket.error:
        logger.exception("Unable to listen()")
        sock.close()
        sock = None
        raise

    return sock


def __zerosend(left, fsize, file_obj, client_s):
    bys = min(left, fsize)

    # pylint: disable=no-member
    client_s.sendfile(file_obj, count=bys)
    logger.debug("Sent %d bytes of data", bys)
    return bys


def __send(left, bufsize, iofilter, client_s):
    bys = min(left, bufsize)
    bytes_obj, ctrl_num = iofilter.read(bys)

    # pylint: disable=no-member
    num_sent = client_s.send(bytes_obj)

    if logger.isEnabledFor(logging.DEBUG):
        bytes_summary = bytes(bytes_obj[:50])
        logger.debug("Sent %d bytes of data (summary: %r%s)",
                     num_sent,
                     bytes_summary,
                     '...' if len(bytes_obj) > len(bytes_summary) else '')

    return num_sent, ctrl_num


def __do_start(args_ns):
    logger.info("[bufsize: %d bytes] [zerocopy: %r]",
                args_ns.bufsize, args_ns.zerocopy)

    sock = __setup_socket(args_ns.bind_addr, args_ns.port)

    file_obj = __validate_file(args_ns.filename, args_ns.size)
    fsize = os.fstat(file_obj.fileno()).st_size
    if not fsize:
        raise RuntimeError("Invalid file size", fsize)

    if not args_ns.zerocopy:
        classobj = Util.get_classobj_of(args_ns.method[0], type(file_obj))
        iofilter = classobj.create(
            file_obj, args_ns.bufsize, extra_args=args_ns.method[1:])

    logger.info("Ready to send %d bytes using data file size of %d bytes",
                args_ns.size, fsize)

    logger.info("Listening socket bound to port %d", args_ns.port)
    try:
        (client_s, client_addr) = sock.accept()
        # If successful, we now have TWO sockets
        #  (1) The original listening socket, still active
        #  (2) The new socket connected to the client
    except socket.error:
        logger.exception("Unable to accept()")
        sock.close()
        sock = None
        file_obj.close()
        if not args_ns.zerocopy:
            iofilter.close()
        raise

    logger.info("Accepted incoming connection %s from client. \
Sending data ...", client_addr)

    left = args_ns.size
    total_sent = 0

    t_start = dt.now().timestamp()
    try:
        while left > 0:
            if args_ns.zerocopy:
                ctrl_num = __zerosend(left, fsize, file_obj, client_s)
                total_sent += ctrl_num
            else:
                num_sent, ctrl_num = __send(
                    left, args_ns.bufsize, iofilter, client_s)
                total_sent += num_sent

            left -= ctrl_num

    # pylint: disable=undefined-variable
    except (ConnectionResetError, BrokenPipeError):
        logger.warning("Connection closed by client")
        if args_ns.zerocopy:
            # File position is updated on socket.sendfile() return or also
            # in case of error in which case file.tell() can be used to
            # figure out the number of bytes which were sent.
            # https://docs.python.org/3/library/socket.html#socket.socket.sendfile
            num_sent = file_obj.tell()
            left -= num_sent
            total_sent += num_sent
    except ValueError:
        logger.exception(
            "Fail to read data from buffered stream %r", file_obj.name)
    finally:
        __make_summary(args_ns,
                       t_start,
                       left,
                       iofilter.get_count(),
                       total_sent)

        client_s.close()
        sock.close()
        sock = None
        file_obj.close()
        if not args_ns.zerocopy:
            iofilter.close()
        logger.info("Resources closed, now exiting")


def __make_summary(args_ns, t_start, left, total_raw_bytes_read, total_sent):
    t_dur = dt.now().timestamp() - t_start
    total_read = args_ns.size - left

    raw_bytes_read_info = ''
    if not args_ns.zerocopy:
        if total_raw_bytes_read:
            raw_bytes_read_info = ' (raw {:d} bytes, {:.3f}%)'.format(
                total_raw_bytes_read,
                total_read / total_raw_bytes_read * 100)

    logger.info("[SUMMARY] [Sent: %d bytes] [Read: %d bytes%s] \
[Duration: %s seconds] [Bitrate: %s bit/s]",
                total_sent,
                total_read,
                raw_bytes_read_info,
                t_dur,
                total_sent * 8 / t_dur)


def main():
    """Entrypoint function."""
    prog_desc = 'Simple network socket server with customized \
workload support.'

    parser = ParameterParser(description=prog_desc)
    start_parser = parser.prepare(BufferedIOBase)
    __populate_start_parser(start_parser)

    parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s | %(name)-16s | \
%(levelname)-8s | PID=%(process)d | %(message)s',
        level=logging.DEBUG)
    logger = logging.getLogger('server')  # pylint: disable=C0103

    main()
