[![Build Status](https://img.shields.io/travis/justas-/py3iperf3.svg)](https://travis-ci.org/justas-/py3iperf3) [![Coverage Status](https://img.shields.io/coveralls/github/justas-/py3iperf3.svg)](https://coveralls.io/github/justas-/py3iperf3?branch=master)

# Py3iPerf3 - A native Python iPerf3 client

Py3iPerf3 is a clone of iPerf3 network performance measurement tool implemented in pure Python. The client is network-protocol compatible with the [original iPerf3 tool](https://github.com/esnet/iperf) maintained by ESnet and written in C. Py3iPerf3 can be used as a stand-alone application, or as a library in your application.

### N.B.

This is work in progress. At the moment, the client supports working as a client (i.e. not server) and can send and receive data using TCP and UDP. 

### Usage

Following the example of iPerf3, the client is a command-line based tool. You can get the list of supported command line options by running the client with the "-h" option: ```python3 iperf.py -h```.

For your convenience, the supported options are listed here:

```
python3 iperf.py
```

### License and contributing

The code of py3iPerf3 is released under the MIT license. Contributions are encouraged via GitHub.
