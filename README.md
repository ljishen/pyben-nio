# Simple Python Network Socket Benchmark

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
./run [-c|s] --help
```

#### Print Socket Server Help Message
```bash
$ docker run --rm ljishen/pyben-nio --server --help
usage: server.py [-h] -b BIND -s SIZE [-p PORT] [-f FILENAME] [-l BUFSIZE]
                 [-z]

Simple network socket server.

optional arguments:
  -h, --help            show this help message and exit
  -b BIND, --bind BIND  Bind to host, one of this machine's outbound interface
  -s SIZE, --size SIZE  The total size of raw data I/O #[BKMG]
  -p PORT, --port PORT  The port for the server to listen on (default: 8881)
  -f FILENAME, --filename FILENAME
                        Read from this file and write to the network, instead
                        of generating a temporary file with random data
  -l BUFSIZE, --bufsize BUFSIZE
                        The maximum amount of data in bytes to be sent at once
                        (default: 4096) #[BKMG]
  -z, --zerocopy        Use "socket.sendfile()" instead of "socket.send()".
```

#### Print Socket Client Help Message
```bash
$ docker run --rm ljishen/pyben-nio --client --help
usage: client.py [-h] -a ADDRESS -s SIZE [-p PORT] [-l BUFSIZE]

Simple network socket client.

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        The host name or IP address the server is running on
  -s SIZE, --size SIZE  The total size of raw data I/O #[BKMG]
  -p PORT, --port PORT  Same as the server port for the client to connect to
                        (default: 8881)
  -l BUFSIZE, --bufsize BUFSIZE
                        The maximum amount of data in bytes to be received at
                        once (default: 4096) #[BKMG]
```
