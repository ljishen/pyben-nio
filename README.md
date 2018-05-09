# Pyben-nio

Simple Python Network Socket Benchmark.


## Supported Architectures

- amd64
- arm64v8


## Usage


```bash
# Create data_file to be used by the server
$ fallocate -l 1g data_file

# Start the socket server
$ docker run --rm -ti --network host \
    -v "$(pwd)"/data_file:/root/data_file \
    ljishen/pyben-nio \
    --server -b localhost -s 1g -f /root/data_file -z

# Start the socket client
$ docker run --rm -ti --network host ljishen/pyben-nio --client -s 1g -a localhost
```

#### Print General Help Message
```bash
$ docker run --rm ljishen/pyben-nio --help
Usage: ./run [--client|server] [OPTIONS]

Simple network socket benchmark.

optional arguments:
  -h, --help            show this help message and exit
  --client              Run in the client mode
  --server              Run in the server mode

For detail options for the respective mode, run
./run [--client|server] --help
```

#### Print Socket Server Help Message
```bash
$ docker run --rm ljishen/pyben-nio --server --help
usage: server.py [-h] -b BIND -s SIZE [-p PORT] [-f FN] [-l BS] [-z]

Simple network socket server.

optional arguments:
  -h, --help            show this help message and exit
  -b BIND, --bind BIND  Bind to host, one of this machine's outbound interface
  -s SIZE, --size SIZE  The total size of raw data I/O ([BKMG])
  -p PORT, --port PORT  The port for the server to listen on (default: 8881)
  -f FN, --filename FN  Read from this file and write to the network, instead
                        of generating a temporary file with random data
  -l BS, --bufsize BS   The maximum amount of data in bytes to be sent at once
                        (default: 4096) ([BKMG])
  -z, --zerocopy        Use "socket.sendfile()" instead of "socket.send()".

[BKMG] indicates options that support a B/K/M/G (b/kb/mb/gb) suffix for byte,
kilobyte, megabyte, or gigabyte
```

#### Print Socket Client Help Message
```bash
$ docker run --rm ljishen/pyben-nio --client --help
usage: client.py [-h] -a ADDRS [ADDRS ...] -s SIZE [-p PORT] [-b BIND] [-l BS]

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

[BKMG] indicates options that support a B/K/M/G (b/kb/mb/gb) suffix for byte,
kilobyte, megabyte, or gigabyte
```


## Miscellaneous

#### Commands to Create the Docker Image Manifest

```bash
docker manifest create ljishen/pyben-nio ljishen/pyben-nio:amd64 ljishen/pyben-nio:arm64v8
docker manifest annotate ljishen/pyben-nio ljishen/pyben-nio:amd64 --os linux --arch amd64
docker manifest annotate ljishen/pyben-nio ljishen/pyben-nio:arm64v8 --os linux --arch arm64 --variant v8
docker manifest push ljishen/pyben-nio
```

References: [Create and use multi-architecture docker images](https://developer.ibm.com/linuxonpower/2017/07/27/create-multi-architecture-docker-image/)
