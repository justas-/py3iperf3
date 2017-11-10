import asyncio
import logging
import struct
import time

from py3iperf3.tcp_test_protocol import TcpTestProtocol
from py3iperf3.iperf3_api import Iperf3TestProto

class TestStream(object):
    """A single test data stream"""

    def __init__(self, **kwargs):
        self._loop = kwargs.get('loop')
        self._test = kwargs.get('test')

        self.done = False

        self._test_protocol = None
        self._sending_handle = None

        self._time_stream_start = None
        self._time_stream_stop = None

        self._bytes_tx_this_interval = 0
        self._bytes_rx_this_interval = 0
        self._blocks_tx_this_interval = 0
        self._pkt_tx_this_interval = 0
        self._pkt_rx_this_interval = 0

    def get_stream_interval_stats(self):
        """Get (and reset) interval stats"""

        # TODO: Change for TCP/UDP

        if self._test.sender:
            num_bytes = self._bytes_tx_this_interval
        else:
            num_bytes = self._bytes_rx_this_interval

        stats = {
		    "socket":	        1,
			"start":	        None,
			"end":	            None,
			"seconds":	        None,
			"bytes":	        num_bytes,
			"bits_per_second":	None,
			"retransmits":	    0,
			"snd_cwnd":	        0,
			"omitted":	        False
        }

        self._bytes_rx_this_interval = 0
        self._bytes_tx_this_interval = 0
        self._blocks_tx_this_interval = 0
        self._pkt_tx_this_interval = 0
        self._pkt_rx_this_interval = 0

        return stats

    def create_connection(self):
        """Create protocol connection to the server"""

        try:
            connect_coro = self._loop.create_connection(
                lambda: TcpTestProtocol(test_stream=self),
                self._test.server_address,
                self._test.server_port)
            self._loop.create_task(connect_coro)
        except Exception as exc:
            logging.exception('Exception connecting to the server!', exc_info=exc)

    def connection_established(self, test_protocol):
        """Call-back: Connection to the server established"""

        self._test_protocol = test_protocol
        self._test_protocol.send_data(
            self._test.cookie.encode('ascii'))

        logging.info('Stream: Sent cookie')

    def data_received(self, data):
        """Call-back: Data received on the test data connection"""
        self._bytes_rx_this_interval += len(data)

        if self._test.data_protocol == Iperf3TestProto.UDP:
            self._pkt_rx_this_interval += 1

    def _send_block(self):
        """Send data over the test protocol"""

        data_block = self._get_block()
        self._test_protocol.send_data(data_block)

        self._blocks_tx_this_interval += 1
        self._bytes_tx_this_interval += self._test.block_size

        if self._test.data_protocol == Iperf3TestProto.UDP:
            self._pkt_tx_this_interval += 1

        self._sending_handle = self._loop.call_soon(self._send_block)

    def _get_block(self):
        """Get data block for sending"""

        if self._test.data_protocol == Iperf3TestProto.TCP:
            data_block = bytearray()
            data_block.extend(self._test.block_size * bytes([127]))

            return data_block
        
        elif self._test.data_protocol == Iperf3TestProto.UDP:
            # Do some magic
            return None

    def start_stream(self):
        """Start sending data"""

        logging.debug('Start stream called')
        self._time_stream_start = time.time()

        if self._sending_handle is None:
            self._sending_handle = self._loop.call_soon(self._send_block)

    def stop_stream(self):
        """Stop sending data"""

        logging.debug('Stop stream called')
        self._time_stream_stop = time.time()

        if self._sending_handle is not None:
            self._sending_handle.cancel()
            self._sending_handle = None

        self.done = True
