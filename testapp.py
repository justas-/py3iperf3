import logging
import asyncio
import os

from py3iperf3.iperf3_client import Iperf3Client
from py3iperf3.utils import setup_logging

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    params = {
        'server_address':'127.0.0.1',
        'server_port':5201,
        'client_port':1337,
        'ip_version':4,
        'debug': True,
        'log_filename':r'C:\py\test.txt',
        'format':'g',
        'parallel':3,
        'blockcount':100,
    }

    setup_logging(**params)

    iperf3_client = Iperf3Client(loop=loop)
    iperf3_test = iperf3_client.create_test(test_parameters=params)

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

    logging.info('Closing client')
    iperf3_client.stop_all_tests()
    loop.close()
    logging.shutdown()
