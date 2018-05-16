#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime as dt
from importlib import import_module
from pkgutil import walk_packages

import logging
import os
import socket
import sys
import tempfile
import methods

from converter import Converter
from version import MyVersionAction
from paramparser import ParameterParser


def __list_methods():
    return [name for _, name, _ in walk_packages(methods.__path__)
            if name != 'iofilter']


def __get_classobj_of(method: str):
    return getattr(
        import_module('.' + method, methods.__package__),
        method.capitalize())


START_PARSER_NAME = 'start'
DESC_PARSER_NAME = 'desc'


def __create_start_parser(subparsers):
    start_parser = subparsers.add_parser(
        START_PARSER_NAME,
        epilog='[BKMG] indicates options that support a \
                B/K/M/G (b/kb/mb/gb) suffix for \
                byte, kilobyte, megabyte, or gigabyte')

    start_parser.add_argument(
        '-b', '--bind', type=str,
        help='Bind to host, one of this machine\'s outbound interface',
        required=DESC_PARSER_NAME not in sys.argv)
    start_parser.add_argument(
        '-s', '--size', type=str,
        help='The total size of raw data I/O ([BKMG])',
        required=DESC_PARSER_NAME not in sys.argv)
    start_parser.add_argument(
        '-p', '--port', type=int,
        help='The port for the server to listen on (default: 8881)',
        default=8881,
        required=False)
    start_parser.add_argument(
        '-f', '--filename', metavar='FN', type=str,
        help='Read from this file and write to the network, \
              instead of generating a temporary file with random data',
        required=False)
    start_parser.add_argument(
        '-l', '--bufsize', metavar='BS', type=str,
        help='The maximum amount of data in bytes to be sent at once \
              (default: 4096) ([BKMG])',
        default='4K',
        required=False)
    start_parser.add_argument(
        '-d', '--debug', action='store_true',
        help='Show debug messages',
        default=False,
        required=False)

    # Since socket.sendfile() performs the data reading and sending within
    # the kernel space, there is no user space function can inject into
    # during this process. Therefore the zerocopy option conflicts with the
    # method option.
    group = start_parser.add_mutually_exclusive_group()
    start_parser.set_special_dest('method')
    group.add_argument(
        '-m', '--method', type=str,
        help='The data filtering method to apply on reading from the file \
              (default: raw)',
        choices=__list_methods(),
        default='raw',
        required=False)
    group.add_argument(
        '-z', '--zerocopy', action='store_true',
        help='Use "socket.sendfile()" instead of "socket.send()".',
        required=False)


def __create_desc_parser(subparsers):
    desc_parser = subparsers.add_parser(DESC_PARSER_NAME)
    desc_parser.add_argument(
        '-m', '--method', type=str,
        help='Show description messages for specific data filtering method',
        choices=__list_methods(),
        required=START_PARSER_NAME not in sys.argv)
    desc_parser.add_argument(
        '-d', '--debug', action='store_true',
        help='Show debug messages',
        default=False,
        required=False)


def __get_args():
    prog_desc = 'Simple network socket server with customized read \
workload support.'

    parser = ParameterParser(description=prog_desc)
    MyVersionAction.set_prog_desc(prog_desc)
    parser.add_argument('-v', '--version', action=MyVersionAction,
                        version='%(prog)s version 1.1')

    subparsers = parser.add_subparsers(
        dest='subparser_name',
        help='Select either command to show more messages')

    __create_start_parser(subparsers)
    __create_desc_parser(subparsers)

    args = parser.parse_args()

    if not args.debug:
        logging.disable(logging.DEBUG)

    if args.subparser_name == DESC_PARSER_NAME:
        __get_classobj_of(args.method).print_desc()
        parser.exit()

    bind_addr = args.bind
    size = Converter.human2bytes(args.size)
    port = args.port
    filename = args.filename
    bufsize = Converter.human2bytes(args.bufsize)
    method = args.method.split()
    zerocopy = args.zerocopy

    return bind_addr, size, port, filename, bufsize, method, zerocopy


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
        file_obj.flush()
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


def main():
    bind_addr, size, port, filename, bufsize, method, zerocopy = __get_args()
    logger.info("[bufsize: %d bytes] [zerocopy: %r]", bufsize, zerocopy)

    sock = __setup_socket(bind_addr, port)

    file_obj = __validate_file(filename, size)
    fsize = os.fstat(file_obj.fileno()).st_size
    if not fsize:
        raise RuntimeError("Invalid file size", fsize)

    if not zerocopy:
        classobj = __get_classobj_of(method[0])
        iofilter = classobj.create(file_obj, extra_args=method[1:])

    logger.info("Ready to send %d bytes using data file size of %d bytes",
                size, fsize)

    logger.info("Listening socket bound to port %d", port)
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
        raise

    logger.info("Accepted incoming connection %s from client. \
Sending data ...", client_addr)

    left = size
    t_start = dt.now().timestamp()
    try:
        while left > 0:
            if zerocopy:
                bys = min(left, fsize)
                client_s.sendfile(file_obj, count=bys)
                logger.debug("Sent %d bytes of data", bys)
                left -= bys
            else:
                bys = min(left, bufsize)
                bytes_obj = iofilter.read(bys)

                sent = client_s.send(bytes_obj)
                left -= sent
                logger.debug("Sent %d bytes of data", sent)
    except (ConnectionResetError, BrokenPipeError):
        logger.warn("Connection closed by client")
        if zerocopy:
            # File position is updated on socket.sendfile() return or also
            # in case of error in which case file.tell() can be used to
            # figure out the number of bytes which were sent.
            # https://docs.python.org/3/library/socket.html#socket.socket.sendfile
            left -= file_obj.tell()
    finally:
        dur = dt.now().timestamp() - t_start
        sent = size - left
        logger.info("Total sent %d bytes of data in %s seconds \
(bitrate: %s bit/s)",
                    sent, dur, sent * 8 / dur)
        client_s.close()
        sock.close()
        sock = None
        file_obj.close()
        logger.info("Sockets closed, now exiting")


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s | %(name)-16s | %(levelname)-8s | %(message)s',
        level=logging.DEBUG)
    logger = logging.getLogger('server')  # pylint: disable=C0103

    main()
