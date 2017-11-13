"""
A class representing a single data stream in iPerf3 test.
"""
import logging
import time

from py3iperf3.tcp_test_protocol import TcpTestProtocol
from py3iperf3.iperf3_api import Iperf3TestProto

class TestStream(object):
    """A single test data stream"""

    def __init__(self, **kwargs):
        self._loop = kwargs.get('loop')
        self._test = kwargs.get('test')
        self._logger = logging.getLogger('py3iperf3')

        self.done = False

        self._test_protocol = None
        self._sending_handle = None

        self._time_stream_start = None
        self._time_stream_stop = None

        self._block_size = self._test.block_size
        self._stop_on = self._test.test_type

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
            self._logger.exception('Exception connecting to the server!', exc_info=exc)

    def connection_established(self, test_protocol):
        """Call-back: Connection to the server established"""

        self._test_protocol = test_protocol
        self._test_protocol.send_data(
            self._test.cookie.encode('ascii'))

        self._logger.info('Stream: Sent cookie')

    def data_received(self, data):
        """Call-back: Data received on the test data connection"""
        self._bytes_rx_this_interval += len(data)

        if self._test.data_protocol == Iperf3TestProto.UDP:
            self._pkt_rx_this_interval += 1

    def _try_sending(self):
        """Check the gating and send if possible"""

        if self._stop_on == 't':
            # Time based test will be stopped by the test class
            self._send_block()
            self._sending_handle = self._loop.call_soon(self._try_sending)

        elif self._stop_on == 'b':
            # Check the remianing block count
            if self._test._blocks_remaining:
                self._test._blocks_remaining -= 1
                self._send_block()
                self._sending_handle = self._loop.call_soon(self._try_sending)

            else:
                # No more blocks to send. Inform test and do not reschedule sending
                self._sending_handle = None
                self.done = True
                self._test.sendable_data_depleted()

        elif self._stop_on == 's':
            # Check the remaining bytes count

            if self._test._bytes_remaining > self._block_size:
                # Send the whole block, reduce size as normal
                self._test._bytes_remaining -= self._block_size
                self._send_block()
                self._sending_handle = self._loop.call_soon(self._try_sending)

            elif self._test._bytes_remaining > 0:
                # Sent the whole block, reduce to 0
                self._test._bytes_remaining = 0
                self._send_block()
                self._sending_handle = None
                self.done = True
                self._test.sendable_data_depleted()

            else:
                self._sending_handle = None
                self.done = True
                self._test.sendable_data_depleted()

    def _send_block(self):
        """Send data over the test protocol"""

        data_block = self._get_block()
        self._test_protocol.send_data(data_block)

        self._blocks_tx_this_interval += 1
        self._bytes_tx_this_interval += self._test.block_size

        if self._test.data_protocol == Iperf3TestProto.UDP:
            self._pkt_tx_this_interval += 1

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

        self._logger.debug('Start stream called')
        self._time_stream_start = time.time()

        if self._sending_handle is None:
            self._sending_handle = self._loop.call_soon(self._send_block)

    def stop_stream(self):
        """Stop sending data"""

        self._logger.debug('Stop stream called')
        self._time_stream_stop = time.time()

        if self._sending_handle is not None:
            self._sending_handle.cancel()
            self._sending_handle = None

        self.done = True
