"""
A class representing a single data stream in iPerf3 test.
"""
import socket

from py3iperf3.data_stream_base import BaseTestStream
from py3iperf3.data_protocol_tcp import TcpTestProtocol
from py3iperf3.utils import data_size_formatter

class TestStreamTcp(BaseTestStream):
    """A single test data stream"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._paused = False

    def print_sum_stats(self, stat_list):
        """Given a list of stats objects print a sum"""

        # Ignore if empty
        if not stat_list:
            return

        sum_bytes = sum([x['bytes'] for x in stat_list])
        sum_bytes_str = data_size_formatter(sum_bytes*8, in_bytes=True)

        t_start = stat_list[0]['start']
        t_end = stat_list[0]['end']
        t_dif = stat_list[0]['seconds']
        speed_str = data_size_formatter(int(sum_bytes * 8 / t_dif), dimmension='m')

        self._logger.info('[{}] {:.2f}-{:.2f} sec {} B {}/sec'.format(
            'SUM',
            t_start,
            t_end,
            sum_bytes_str,
            speed_str))
        self._logger.info('- - - - - - - - - - - - - - - - - - - - - - - - -')

    def create_connection(self):
        """Create protocol connection to the server"""

        if self._test.ip_version == 4:
            ip_family = socket.AF_INET
        else:
            ip_family = socket.AF_INET6

        self._logger.debug('Making outgoing data connection to %s:%s IPver: %s',
                           self._test.server_address,
                           self._test.server_port,
                           ip_family)

        try:
            connect_coro = self._loop.create_connection(
                lambda: TcpTestProtocol(
                    test_stream=self,
                    no_delay=self._test.no_delay,
                    window=self._test.window),
                host=self._test.server_address,
                port=self._test.server_port,
                family=ip_family)
            self._loop.create_task(connect_coro)
        except Exception as exc:
            self._logger.exception('Exception connecting to the server!', exc_info=exc)

    def connection_established(self, test_protocol):
        """Call-back: Connection to the server established"""

        self._test_protocol = test_protocol
        self._test_protocol.send_data(
            self._test.cookie.encode('ascii'))

        self._logger.debug('Stream: Sent cookie')

    def save_stats(self, t_start, t_end, t_sec):
        """
        Save test stats to a stats object.
        """

        # Account for test direction
        if self._test.sender:
            num_bytes = self._bytes_tx_this_interval
        else:
            num_bytes = self._bytes_rx_this_interval

        # Save stats object
        stats = {
		    "socket":	        self._test_protocol.socket_id,
			"start":	        t_start,
			"end":	            t_end,
			"seconds":	        t_sec,
			"bytes":	        num_bytes,
			"bits_per_second":	int(num_bytes * 8 / t_sec),
			"omitted":	        False
        }

        # Reset the counters
        self._bytes_rx_this_interval = 0
        self._bytes_tx_this_interval = 0
        self._blocks_tx_this_interval = 0
        self._pkt_tx_this_interval = 0
        self._pkt_rx_this_interval = 0

        # Save and return
        self._stat_objs.append(stats)
        return stats

    def print_last_stats_entry(self):
        """
        Print sum stats over all time intervals.
        """

        # Get reference to the last entry
        stats = self._stat_objs[-1]

        # Format strings
        size_str = data_size_formatter(int(stats['bytes'])*8, in_bytes=True)
        speed_str = data_size_formatter(int(stats['bits_per_second']))

        # Print entry
        self._logger.info('[{}] {:.2f}-{:.2f} sec {} B {}/sec'.format(
            stats['socket'],
            stats['start'],
            stats['end'],
            size_str,
            speed_str))

    def get_final_stats(self):
        """Get final stats object"""

        stats_obj = {
            "id":self._stream_id,
            "bytes":sum([x['bytes'] for x in self._stat_objs]),
            "retransmits":-1,
            "jitter":0,
            "errors":0,
            "packets":0,
        }

        return stats_obj

    def _try_sending(self):
        """
        Implement paused gating.
        """
        if not self._paused:
            super()._try_sending()

    def pause_writing(self):
        """
        Request by transport to pause writing.
        """
        self._paused = True

        if self._sending_handle:
            self._sending_handle.cancel()
            self._sending_handle = None

    def resume_writing(self):
        """
        Request be transport to resume writing.
        """
        self._paused = False
        self._sending_handle = self._loop.call_soon(self._try_sending)
