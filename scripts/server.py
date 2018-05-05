#!/usr/bin/env python3

import argparse
import logging
import os
import socket
import tempfile

from converter import human2bytes
from datetime import datetime as dt

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] %(message)s',
    level=logging.INFO)


def get_args():
    parser = argparse.ArgumentParser(
        description='Simple network socket server.',
        epilog='[BKMG] indicates options that support a \
                B/K/M/G (b/kb/mb/gb) suffix for \
                byte, kilobyte, megabyte, or gigabyte')

    parser.add_argument(
        '-b', '--bind', type=str,
        help='Bind to host, one of this machine\'s outbound interface',
        required=True)
    parser.add_argument(
        '-s', '--size', type=str,
        help='The total size of raw data I/O ([BKMG])',
        required=True)
    parser.add_argument(
        '-p', '--port', type=int,
        help='The port for the server to listen on (default: 8881)',
        default=8881,
        required=False)
    parser.add_argument(
        '-f', '--filename', metavar='FN', type=argparse.FileType('rb'),
        help='Read from this file and write to the network, \
              instead of generating a temporary file with random data',
        required=False)
    parser.add_argument(
        '-l', '--bufsize', metavar='BS', type=str,
        help='The maximum amount of data in bytes to be sent at once \
              (default: 4096) ([BKMG])',
        default='4K',
        required=False)
    parser.add_argument(
        '-z', '--zerocopy', action='store_true',
        help='Use "socket.sendfile()" instead of "socket.send()".',
        required=False)

    args = parser.parse_args()

    bind_addr = args.bind
    size = human2bytes(args.size)
    port = args.port
    fp = args.filename
    bufsize = human2bytes(args.bufsize)
    zero_copy = args.zerocopy

    return bind_addr, size, port, fp, bufsize, zero_copy


def main():
    bind_addr, size, port, fp, bufsize, zero_copy = get_args()
    logging.info("bufsize: %d bytes, zero_copy: %r", bufsize, zero_copy)

    # Create TCP socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        logging.exception("Could not create socket")
        raise

    # Bind to listening port
    try:
        # The SO_REUSEADDR flag tells the kernel to reuse a local socket
        # in TIME_WAIT state, without waiting for its natural timeout to
        # expire.
        # See https://docs.python.org/3.6/library/socket.html#example
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        s.bind((bind_addr, port))
    except socket.error:
        logging.exception("Unable to bind on port %d", port)
        s.close()
        s = None
        raise

    # Listen
    try:
        s.listen(1)
    except socket.error:
        logging.exception("Unable to listen()")
        s.close()
        s = None
        raise

    try:
        if not fp:
            fp = tempfile.TemporaryFile('w+b')
            logging.info("Generating temporary file of size %d bytes ...",
                         size)
            fp.write(os.urandom(size))
            fp.flush()

        fsize = os.fstat(fp.fileno()).st_size
        if not fsize:
            raise RuntimeError("Invalid file size", fsize)

        logging.info("Ready to send %d bytes using data file size of %d bytes",
                     size, fsize)

        logging.info("Listening socket bound to port %d", port)
        try:
            (client_s, client_addr) = s.accept()
            # If successful, we now have TWO sockets
            #  (1) The original listening socket, still active
            #  (2) The new socket connected to the client
        except socket.error:
            logging.exception("Unable to accept()")
            s.close()
            s = None
            raise

        logging.info("Accepted incoming connection %s from client. \
Sending data ...", client_addr)

        t_start = dt.now().timestamp()
        try:
            left = size
            while left > 0:
                if zero_copy:
                    bys = min(left, fsize)
                    client_s.sendfile(fp, count=bys)
                    logging.debug("Sent %d bytes of data", bys)
                    left -= bys
                else:
                    bys = min(left, bufsize)
                    bytes_obj = fp.read(bys)

                    if not bytes_obj:
                        fp.seek(0)
                        continue

                    if len(bytes_obj) < bys:
                        fp.seek(0)

                    sent = client_s.send(bytes_obj)
                    left -= sent
                    logging.debug("Sent %d bytes of data", sent)
        except (ConnectionResetError, BrokenPipeError) as es:
            logging.warn("Connection closed by client")
            if zero_copy:
                # File position is updated on socket.sendfile() return or also
                # in case of error in which case file.tell() can be used to
                # figure out the number of bytes which were sent.
                # https://docs.python.org/3/library/socket.html#socket.socket.sendfile
                left -= fp.tell()
        finally:
            dur = dt.now().timestamp() - t_start
            sent = size - left
            logging.info("Total sent %d bytes of data in %s seconds \
(bitrate: %s bit/s)",
                         sent, dur, sent * 8 / dur)
            client_s.close()
            s.close()
            logging.info("Sockets closed, now exiting")
    finally:
        fp.close()


if __name__ == "__main__":
    main()
