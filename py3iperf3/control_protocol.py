import asyncio
import logging
import socket
import binascii

class ControlProtocol(asyncio.Protocol):
    """asyncio protocol for control connection"""

    def __init__(self, test):
        """Initialize the protocol"""

        self._transport = None
        self._test = test
        self._peer_data = None

    def connection_made(self, transport):
        """Connection made callback"""
        self._transport = transport
        self._peer_data = transport.get_extra_info('peername')
        logging.debug('Control connection made! Peer: %s', self._peer_data)
        self._test.server_connection_established(self)

    def connection_lost(self, exc):
        """Connection lost callback"""
        logging.debug('Control connection lost!', exc_info=exc)

    def data_received(self, data):
        """Data received callback"""
        logging.info('Control connection data received. Len: %s bytes', len(data))
        logging.debug('RX data: %s', binascii.hexlify(data))
        self._test.handle_server_message(data)

    def send_data(self, data):
        """Send data over the control connection"""
        self._transport.write(data)

    def close_connection(self):
        """Close connection to the server"""
        logging.debug('Closing connection to the server')
        self._transport.close()

    def get_tcp_mss(self):
        """Get the control socket TCP MSS"""

        # TODO: Win32/Linux compat
        control_socket = self._transport.get_extra_info('socket')
        return control_socket.getsockopt(socket.SOL_SOCKET, socket.TCP_MAXSEG)
