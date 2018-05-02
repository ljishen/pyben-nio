#!/usr/bin/env python3

import argparse
import socket

from datetime import datetime as dt
from convert import human2bytes

MEM_LIMIT = '500MB'


def get_args():
    parser = argparse.ArgumentParser(
        description='Simple network socket client.')

    parser.add_argument(
        '-a', '--address', type=str,
        help='The host name or IP address the server is running on',
        required=True)
    parser.add_argument(
        '-s', '--size', type=str,
        help='The total size of raw data I/O #[BKMG]',
        required=True)
    parser.add_argument(
        '-p', '--port', type=int,
        help='Same as the server port for the client to connect to (default: 8881)',
        default=8881,
        required=False)
    parser.add_argument(
        '-l', '--bufsize', type=str,
        help='The maximum amount of data in bytes to be received at once \
              (default: 4096) #[BKMG]',
        default='4K',
        required=False)

    args = parser.parse_args()

    host_addr = args.address
    size = human2bytes(args.size)
    port = args.port
    bufsize = human2bytes(args.bufsize)

    return host_addr, size, port, bufsize


def main():
    host_addr, size, port, bufsize = get_args()
    print("bufsize:", bufsize, "(bytes)")

    # Create TCP socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print("\nError: could not create socket")
        raise

    print("\nConnecting to server at " + host_addr + " on port " + str(port))

    # Connect to server
    try:
        s.connect((host_addr, port))
    except socket.error:
        print("\nError: Could not connect to the server")
        s.close()
        s = None
        raise

    print("\nConnection established. Receiving data ...")

    mem_limit_bs = human2bytes(MEM_LIMIT)
    left = size
    objs_size = 0
    obj_pool = []

    t_start = dt.now().timestamp()
    try:
        while left > 0:
            bys = min(bufsize, left)
            bytes_obj = s.recv(bys)
            if not bytes_obj:
                break

            obj_s = len(bytes_obj)
            # print("Received", obj_s, "bytes of data")
            obj_pool.append(bytes_obj)
            left -= obj_s
            objs_size += obj_s
            if objs_size > mem_limit_bs:
                del obj_pool[:(len(obj_pool) // 2)]
                objs_size //= 2
    finally:
        t_dur = dt.now().timestamp() - t_start
        print("\nTotal received", (size - left), "bytes of data in", t_dur, "seconds")
        print("(bitrate=" + str((size - left) * 8 / t_dur) + "bit/s)")
        s.close()
        print("\nSockets closed, now exiting")


if __name__ == "__main__":
    main()
