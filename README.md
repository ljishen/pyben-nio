# Pyben-nio

╔═╗┬ ┬┌┐ ┌─┐┌┐┌   ┌┐┌┬┌─┐
╠═╝└┬┘├┴┐├┤ │││───│││││ │
╩   ┴ └─┘└─┘┘└┘   ┘└┘┴└─┘ [![Build Status](https://travis-ci.org/ljishen/pyben-nio.svg?branch=master)](https://travis-ci.org/ljishen/pyben-nio)

Simple Python Network Socket Benchmark with Customized Read Workload Support.

![screenshot](https://user-images.githubusercontent.com/468515/40152383-d759197a-5939-11e8-9547-e2395e9062d3.gif)


## Supported Architectures

[`amd64`](amd64/Dockerfile), [`arm64v8`](arm64v8/Dockerfile)


## Version

- server: `1.1`
- client: `1.0`


## Usage

```bash
# Create data_file to be used by the server
$ fallocate -l 1g data_file

# Start the socket server with data filtering method "linspace"
$ docker run --rm -ti --network host \
    -v "$(pwd)"/data_file:/root/data_file \
    ljishen/pyben-nio \
    --server start \
    -b localhost -s 1g -f /root/data_file -m "linspace step=2"

# Start the socket client
$ docker run --rm -ti --network host \
    ljishen/pyben-nio \
    --client \
    -a localhost -s 1g
```

#### Print Socket Server Help Message
```bash
$ docker run --rm ljishen/pyben-nio --server start --help
usage: server.py start [-h] -b BIND -s SIZE [-p PORT] [-f FN] [-l BS]
                       [-m {linspace,raw} | -z] [-d]

optional arguments:
  -h, --help            show this help message and exit
  -b BIND, --bind BIND  Bind to host, one of this machine's outbound interface
  -s SIZE, --size SIZE  The total size of raw data I/O ([BKMG])
  -p PORT, --port PORT  The port for the server to listen on (default: 8881)
  -f FN, --filename FN  Read from this file and write to the network, instead
                        of generating a temporary file with random data
  -l BS, --bufsize BS   The maximum amount of data in bytes to be sent at once
                        (default: 4096) ([BKMG])
  -m {linspace,raw}, --method {linspace,raw}
                        The data filtering method to apply on reading from the
                        file (default: raw)
  -z, --zerocopy        Use "socket.sendfile()" instead of "socket.send()".
  -d, --debug           Show debug messages

[BKMG] indicates options that support a B/K/M/G (b/kb/mb/gb) suffix for byte,
kilobyte, megabyte, or gigabyte
```

#### Print description of data filtering method `linspace`
```bash
$ docker run --rm ljishen/pyben-nio --server desc -m linspace
-------------------------------------------------------------------------------
[MODULE] methods.linspace
-------------------------------------------------------------------------------
[DESC]   Read evenly spaced bytes from the file.

    The space is defined by the parameter step, which is equals to the
    difference between the index of the current byte and the index of the last
    byte in the source bytes sequence.


[PARAMS] Extra method parameter {'step': <class 'int'>}
-------------------------------------------------------------------------------
```

#### Print Socket Client Help Message
```bash
$ docker run --rm ljishen/pyben-nio --client --help
usage: client.py [-h] -a ADDRS [ADDRS ...] -s SIZE [-p PORT] [-b BIND] [-l BS]
                 [-d] [-v]

Simple network socket client.

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRS [ADDRS ...], --addresses ADDRS [ADDRS ...]
                        The list of host names or IP addresses the servers are
                        running on (separated by space)
  -s SIZE, --size SIZE  The total size of raw data I/O ([BKMG])
  -p PORT, --port PORT  The client connects to the port where the server is
                        listening on (default: 8881)
  -b BIND, --bind BIND  Specify the incoming interface for receiving data,
                        rather than allowing the kernel to set the local
                        address to INADDR_ANY during connect (see ip(7),
                        connect(2))
  -l BS, --bufsize BS   The maximum amount of data in bytes to be received at
                        once (default: 4096) ([BKMG])
  -d, --debug           Show debug messages
  -v, --version         show program's version number and exit

[BKMG] indicates options that support a B/K/M/G (b/kb/mb/gb) suffix for byte,
kilobyte, megabyte, or gigabyte
```


## Miscellaneous

#### Commands to Create the Docker Image Manifest

```bash
docker manifest create ljishen/pyben-nio ljishen/pyben-nio:amd64 ljishen/pyben-nio:arm64v8
docker manifest annotate ljishen/pyben-nio ljishen/pyben-nio:amd64 --os linux --arch amd64
docker manifest annotate ljishen/pyben-nio ljishen/pyben-nio:arm64v8 --os linux --arch arm64 --variant v8

# purge the local manifest after push so that I can
# upgrade the manifest by creating a new one next time.
# https://github.com/docker/for-win/issues/1770
docker manifest push --purge ljishen/pyben-nio
```

References: [Create and use multi-architecture docker images](https://developer.ibm.com/linuxonpower/2017/07/27/create-multi-architecture-docker-image/)
