"""
"""
import struct
import time

from py3iperf3.base_test_stream import BaseTestStream
from py3iperf3.udp_test_protocol import UdpTestProtocol

class TestStreamUdp(BaseTestStream):
    """ """

    def __init__(self, **kwargs):
        """Init the UDP stream"""

        # Init the stream
        super().__init__(**kwargs)

        # Set UDP related values
        self._pkt_cnt = 1
        self._pkt_cnt_64bit = self._test._parameters.udp64bitcounters

    def create_connection(self):
        """ """
        connect_coro = self._loop.create_datagram_endpoint(
            lambda: UdpTestProtocol(test_stream=self),
            remote_addr=(
                self._test.server_address,
                self._test.server_port))
        self._loop.create_task(connect_coro)

    def connection_established(self, test_protocol):
        """ """
        self._test_protocol = test_protocol

        for _ in range(1):
            self._test_protocol.send_data(
                struct.pack('>I',12345678))

        self._logger.info('UDP Test: initial data')

    def data_received(self, data, remote_addr = None):
        self._logger.debug('Got UDP data: %s from: %s',
                           data, remote_addr)
        super().data_received(data, remote_addr)

    def _get_block(self):
        """Get block to send and make UDP changes"""

        block_bytes = super()._get_block()

        time_now = time.time()
        time_sec = int(time_now)
        time_usec = int((time_now % 1) * 1000000)

        # Handle 64-bit counters
        if self._pkt_cnt_64bit:
            udp_extras = struct.pack('>IIQ',
                                 time_sec,
                                 time_usec,
                                 self._pkt_cnt)
            block_bytes = udp_extras + block_bytes[16:]
        else:
            udp_extras = struct.pack('>III',
                                 time_sec,
                                 time_usec,
                                 self._pkt_cnt)
            block_bytes = udp_extras + block_bytes[12:]
        
        return block_bytes

    def _send_block(self):
        """Extend sending function with packets counting"""

        # Send the block
        super()._send_block()

        # Increase the counters
        self._pkt_tx_this_interval += 1
        self._pkt_cnt += 1
