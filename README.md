# Pyben-nio [![Build Status](https://travis-ci.org/ljishen/pyben-nio.svg?branch=master)](https://travis-ci.org/ljishen/pyben-nio)

```bash
╔═╗┬ ┬┌┐ ┌─┐┌┐┌   ┌┐┌┬┌─┐
╠═╝└┬┘├┴┐├┤ │││───│││││ │
╩   ┴ └─┘└─┘┘└┘   ┘└┘┴└─┘
```

Simple Python Network Socket Benchmark with Customized Read Workload Support.

![pyben-nio_demo](https://user-images.githubusercontent.com/468515/40457687-a9d527c8-5eac-11e8-8bd9-8fcae35c7e00.gif)

[View this asciicast on asciinema.org](https://asciinema.org/a/VfGDflAuT0kPQPUyCraJ5WQTE)


## Supported Architectures

[`amd64`](Dockerfile), [`arm64v8`](update.sh)


## Version

- 0.2


## Usage

```bash
# Create data_file to be used by the server
$ fallocate -l 1g data_file

# Start the socket server using data filtering method "match"
# to select the bytes with even int value up to 1GB
$ docker run --rm -ti --network host \
    -v "$(pwd)"/data_file:/root/data_file \
    ljishen/pyben-nio \
    --server start \
    -b localhost -s 1g -f /root/data_file -m "match; func=lambda v: v % 2 == 0"

# Start the socket client also using the method "match"
# to only receive all the bytes of 'a's.
$ docker run --rm -ti --network host \
    ljishen/pyben-nio \
    --client start \
    -a localhost -s 1g -m "match; func=lambda v: v == ord(b'a')"
```

#### Print Socket Server Help Message
```bash
$ docker run --rm ljishen/pyben-nio --server start --help
usage: server.py start [-h] [-d] -b BIND -s SIZE [-p PORT] [-f FN] [-l BS]
                       [-m {linspace,match,raw} | -z]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Show debug messages
  -b BIND, --bind BIND  Bind to host, one of this machine's outbound interface
  -s SIZE, --size SIZE  The total size of data I/O ([BKMG])
  -p PORT, --port PORT  The port for the server to listen on (default: 8881)
  -f FN, --filename FN  Read from this file and write to the network, instead
                        of generating a temporary file with random data
  -l BS, --bufsize BS   The maximum amount of data in bytes to be sent at once
                        (default: 4K) ([BKMG])
  -m {linspace,match,raw}, --method {linspace,match,raw}
                        The data filtering method to apply on reading from the
                        file (default: raw). Use semicolon (;) to separate
                        method parameters
  -z, --zerocopy        Use "socket.sendfile()" instead of "socket.send()".

[BKMG] indicates options that support a B/K/M/G (b/kb/mb/gb) suffix for byte,
kilobyte, megabyte, or gigabyte
```

#### Print description of data filtering method `match`
```bash
$ docker run --rm ljishen/pyben-nio --server desc -m match
-------------------------------------------------------------------------------
[MODULE] methods.match
-------------------------------------------------------------------------------
[DESC]   Read the bytes that match the function check.

    The parameter func defines the function check that whether the read
    operation should return the byte. The checking function should only accpet
    a single argument as an int value representing the byte and return an
    object that subsequently will be used in bytes filtering based on its truth
    value.

    Also see truth value testing in Python 3:
    https://docs.python.org/3/library/stdtypes.html#truth-value-testing

    
[PARAMS] Extra method parameter {'func': typing.Callable[[int], object]}
-------------------------------------------------------------------------------
```

#### Print Socket Client Help Message
```bash
$ docker run --rm ljishen/pyben-nio --client start --help
usage: client.py start [-h] [-d] -a ADDRS [ADDRS ...] -s SIZE [-p PORT]
                       [-b BIND] [-l BS] [-m {linspace,match,raw}]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Show debug messages
  -a ADDRS [ADDRS ...], --addresses ADDRS [ADDRS ...]
                        The list of host names or IP addresses the servers are
                        running on (separated by space)
  -s SIZE, --size SIZE  The total size of data I/O ([BKMG])
  -p PORT, --port PORT  The client connects to the port where the server is
                        listening on (default: 8881)
  -b BIND, --bind BIND  Specify the incoming interface for receiving data,
                        rather than allowing the kernel to set the local
                        address to INADDR_ANY during connect (see ip(7),
                        connect(2))
  -l BS, --bufsize BS   The maximum amount of data in bytes to be received at
                        once (default: 4K) ([BKMG])
  -m {linspace,match,raw}, --method {linspace,match,raw}
                        The data filtering method to apply on reading from the
                        socket (default: raw). Use semicolon (;) to separate
                        method parameters

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
