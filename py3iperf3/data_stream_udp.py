"""
Test data stream over UDP.
"""
import struct
import time

from py3iperf3.data_stream_base import BaseTestStream
from py3iperf3.data_protocol_udp import UdpTestProtocol

class TestStreamUdp(BaseTestStream):
    """
    UDP Test data stream.
    """

    def __init__(self, **kwargs):
        """Init the UDP stream"""

        # Init the stream
        super().__init__(**kwargs)

        # Set UDP related values
        self._pkt_cnt = 0
        self._pkt_cnt_64bit = self._test._parameters.udp64bitcounters
        self._err_count = 0
        self._ooo_count = 0

        self._jitter = 0
        self._prev_transit = 0

    def create_connection(self):
        """
        Create UDP datagram socket.
        """
        connect_coro = self._loop.create_datagram_endpoint(
            lambda: UdpTestProtocol(test_stream=self),
            remote_addr=(
                self._test.server_address,
                self._test.server_port))
        self._loop.create_task(connect_coro)

    def connection_established(self, test_protocol):
        """
        Callback on connection established.
        """
        self._test_protocol = test_protocol

        for _ in range(1):
            self._test_protocol.send_data(
                struct.pack('>I', 12345678))

        self._logger.info('UDP Test: initial data')

    def data_received(self, data, remote_addr=None):
        """Data received callback"""

        # Ignore '123456789'
        if len(data) == 4:
            return

        # Extract time and packet count
        if self._pkt_cnt_64bit:
            (time_sec, time_usec, pkt_num) = struct.unpack(
                '>IIQ', data[:16])
        else:
            (time_sec, time_usec, pkt_num) = struct.unpack(
                '>III', data[:12])

        # Handle Out-Of-Order packets
        # Algo is lifted from ESnet iPerf3 code
        if pkt_num >= self._pkt_cnt + 1:

            # count errors
            if pkt_num > self._pkt_cnt + 1:
                self._err_count += (pkt_num - 1) - self._pkt_cnt

            # Update largest seen
            self._pkt_cnt = pkt_num
        else:
            self._ooo_count += 1
            if self._err_count > 0:
                self._err_count -= 1

            self._logger.debug("Out-of-Order Packet: Incoming seq: %s but expected %s",
                               pkt_num, self._pkt_cnt)

        # Jitter calc
        transit = time.time() - time_sec - (time_usec / 1000000)
        d = transit - self._prev_transit
        if d < 0:
            d = -d

        self._prev_transit = transit
        self._jitter += (d - self._jitter) / 16.0

        # Handle received data as normal
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
