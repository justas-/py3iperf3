import asyncio
import logging
import struct

from py3iperf3.tcp_test_protocol import TcpTestProtocol

class TestStream(object):
    """description of class"""

    def __init__(self, **kwargs):
        self._loop = kwargs.get('loop')
        self._test = kwargs.get('test')

        self.done = False

        self._test_protocol = None
        self._sending_handle = None

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

        self._test_protocol = test_protocol
        self._test_protocol.send_data(
            self._test.cookie.encode('ascii'))

        logging.info('Stream: Sent cookie')

    def _bulk_send(self, num_bytes=131072):
        """Perform send of num_bytes"""

        # Are we done?
        if self.done:
            return

        msg_data = bytearray()
        msg_data.extend(num_bytes * bytes([127]))

        self._test_protocol.send_data(msg_data)

        self._sending_handle = self._loop.call_soon(self._bulk_send)

    def start_stream(self):
        """Start sending data"""

        logging.debug('Start stream called')

        if self._sending_handle is None:
            self._sending_handle = self._loop.call_soon(self._bulk_send)

    def stop_stream(self):
        """Stop sending data"""

        logging.debug('Stop stream called')

        if self._sending_handle is not None:
            self._sending_handle.cancel()
            self._sending_handle = None

        self.done = True

