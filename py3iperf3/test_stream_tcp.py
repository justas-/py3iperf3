"""
A class representing a single data stream in iPerf3 test.
"""

from py3iperf3.base_test_stream import BaseTestStream
from py3iperf3.tcp_test_protocol import TcpTestProtocol

class TestStreamTcp(BaseTestStream):
    """A single test data stream"""
        
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
