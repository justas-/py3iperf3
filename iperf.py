"""
A Python native iPerf3 client.
"""

import asyncio
import argparse
import logging

from py3iperf3.utils import setup_logging
from py3iperf3.iperf3_client import Iperf3Client

def run_client(params):
    """Runt the client"""

    loop = asyncio.get_event_loop()

    setup_logging(**params)

    iperf3_client = Iperf3Client(loop=loop)
    iperf3_test = iperf3_client.create_test(test_parameters=params)

    # Ensure KeyboardIrq works on Windows
    if os.name == 'nt':
        def wakeup():
            # Call again later
            loop.call_later(0.5, wakeup)
        loop.call_later(0.5, wakeup)

    try:
        loop.call_soon(iperf3_client.run_all_tests)
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    iperf3_client.stop_all_tests()
    loop.close()
    logging.shutdown()

def main():
    """Program entry point"""

    # Setup an argument parser
    parser = argparse.ArgumentParser(description='A Python native iPerf3 client')

    # TODO Args
    
    # Parse the command line params
    params = parser.parse_args()

    # Run the client
    run_client(params)

if __name__ == '__main__':
    main()