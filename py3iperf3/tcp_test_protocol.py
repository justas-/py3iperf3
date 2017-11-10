import asyncio
import logging

class TcpTestProtocol(asyncio.Protocol):
    """description of class"""

    def __init__(self, test_stream=None):
        self._transport = None
        self._stream = test_stream

    def connection_made(self, transport):
        self._transport = transport
        self._peer_data = transport.get_extra_info('peername')
        logging.debug('TCP Test connection made! Peer: %s', self._peer_data)

        self._stream.connection_established(self)

    def data_received(self, data):
        logging.debug('Received %s bytes', len(data))

    def connection_lost(self, exc):
        logging.debug('Connection lost!', exc_info=exc)

    def send_data(self, data):
        self._transport.write(data)


