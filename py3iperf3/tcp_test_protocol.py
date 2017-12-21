import asyncio
import logging
import socket

class TcpTestProtocol(asyncio.Protocol):
    """description of class"""

    def __init__(self, test_stream=None, no_delay=False, window=None, server=None):
        self._transport = None
        self._socket = None
        self._stream = test_stream
        self._logger = logging.getLogger('py3iperf3')
        self._sock_id = None
        self._no_delay = no_delay
        self._window = window
        self._server = server

    @property
    def socket_id(self):
        """Return socket id"""
        return self._sock_id

    def set_owner(self, owner, is_stream = False):
        """Update owner to test from server once ready"""
        if is_stream:
            self._logger.debug('TCP Proto Stream is set!')
            self._stream = owner
        else:
            self._server = owner

    def connection_made(self, transport):
        """Connection established call-back"""

        self._transport = transport
        self._socket = transport.get_extra_info('socket')
        self._sock_id = self._socket.fileno()

        if self._server is None:
            # This is client connecting to the server
            self.connection_to_server_made(transport)
        else:
            # This is incomming connection from the client
            self.connection_from_client(transport)

    def connection_from_client(self, transport):
        """Connection from the client established to the server"""
        peer_data = transport.get_extra_info('peername')
        self._logger.info('[%s] incomming connection from %s port %s',
                          self._sock_id, peer_data[0], peer_data[1])

        self._server.tcp_connection_established(self)

    def connection_to_server_made(self, transport):
        """Connecton to the server established"""

        local_data = self._socket.getsockname()
        peer_data = transport.get_extra_info('peername')

        self._logger.info('[%s] local %s port %s connected to %s port %s',
                          self._sock_id, local_data[0], local_data[1],
                          peer_data[0], peer_data[1])

        # No delay OFF -> Nagle's alg used
        self._socket.setsockopt(
            socket.IPPROTO_TCP,
            socket.TCP_NODELAY,
            0)

        # If required - turn off Nagle's alg (No Delay ON)
        if self._no_delay:
            self._socket.setsockopt(
                socket.IPPROTO_TCP,
                socket.TCP_NODELAY,
                1)

        # Set Socket TX/RX buffer sizes if specified
        if self._window:
            self._logger.debug('Setting socket buffer sizes to %s B', self._window)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self._window)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self._window)

        # Print current buf sizes:
        rx_buf = self._socket.getsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF)
        tx_buf = self._socket.getsockopt(
                socket.SOL_SOCKET,
                socket.SO_SNDBUF)

        self._logger.debug('Socket TX buffer: %s B; RX buffer: %s B;',
                           tx_buf, rx_buf) 

        self._stream.connection_established(self)

    def data_received(self, data):
        """Data received call-back"""
        #self._logger.debug('Received %s bytes', len(data))

        # Inform server that we have data until the stream is ready
        if self._stream is None:
            self._server.control_data_received(self, data)
        else:
            self._stream.data_received(data)

    def connection_lost(self, exc):
        self._logger.debug('[%s] Connection lost!', self._sock_id, exc_info=exc)

    def send_data(self, data):
        self._transport.write(data)
