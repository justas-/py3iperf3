"""
A Python native iPerf3 client.
"""

import asyncio
import argparse
import logging
import os

from py3iperf3.utils import setup_logging
from py3iperf3.iperf3_client import Iperf3Client
from py3iperf3.iperf3_api import Iperf3TestProto
from py3iperf3.iperf3_server import Iperf3Server

def run(params):
    """Runt the client"""

    loop = asyncio.get_event_loop()
    params = vars(params)

    print(params)

    setup_logging(**params)

    if params['server']:
        server = Iperf3Server(params, loop=loop)
    else:
        iperf3_client = Iperf3Client(loop=loop)
        iperf3_client.create_test(test_parameters=params)

    # Ensure KeyboardIrq works on Windows
    if os.name == 'nt':
        def wakeup():
            """Fake wakeup"""
            # Call again later
            loop.call_later(0.5, wakeup)
        loop.call_later(0.5, wakeup)

    try:
        if params['server']:
            server.start_server()
        else:
            loop.call_soon(iperf3_client.run_all_tests)
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Cleanup on exit
    if params['server']:
        server.stop_server()
    else:
        iperf3_client.stop_all_tests()

    loop.close()
    logging.shutdown()

def main():
    """Program entry point"""

    # Setup an argument parser
    parser = argparse.ArgumentParser(description='A Python native iPerf3 client')

    parser.add_argument('--server', help='Run in server mode', action='store_true')
    parser.add_argument('--one-off', help='Process a single client and exit', action='store_true')
    parser.add_argument('--server-address', help='IP Address of the remote peer')
    parser.add_argument('--server-port', help='Port to connect to', type=int)
    parser.add_argument('--client-port', help='Bind lcient to the given port', type=int)
    parser.add_argument('--ip-version', help='Use IP version <4|6>', type=int)
    parser.add_argument('--test-duration', help='Run test for given number of seconds', type=int)
    parser.add_argument('--debug', help='Enable debug output', action='store_true')
    parser.add_argument('--log-filename', help='Log to the indicated file')
    parser.add_argument('--parallel', help='Number of parallel streams to send data', type=int)
    parser.add_argument('--blockcount', help='Number of blocks to send', type=int)
    parser.add_argument('--reverse', help='Server instead of client sends data', action='store_true')
    parser.add_argument('--protocol', help='Transport protocol for sending data <TCP|UDP>')
    parser.add_argument('--no-delay', help='Disable Nagle\'s algorithm', action='store_true')
    parser.add_argument('--title', help='Add free text to the results')
    parser.add_argument('--get-server-output', help='Get results from the server', action='store_true')
    parser.add_argument('--window', help='Set Socket TX/RX buffer size in Bytes', type=int)

    # Parse the command line params
    params = parser.parse_args()

    if not params.protocol:
        params.protocol = Iperf3TestProto.TCP
    else:
        if params.protocol == 'UDP':
            params.protocol = Iperf3TestProto.UDP
        else:
            params.protocol = Iperf3TestProto.TCP

    # Run the client
    run(params)

if __name__ == '__main__':
    main()
