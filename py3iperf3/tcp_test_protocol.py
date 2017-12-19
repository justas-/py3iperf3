import asyncio
import logging
import socket

class TcpTestProtocol(asyncio.Protocol):
    """description of class"""

    def __init__(self, test_stream=None, no_delay=False, window=None):
        self._transport = None
        self._stream = test_stream
        self._logger = logging.getLogger('py3iperf3')
        self._sock_id = None
        self._no_delay = no_delay
        self._window = window

    @property
    def socket_id(self):
        """Return socket id"""
        return self._sock_id

    def connection_made(self, transport):
        self._transport = transport
        peer_data = transport.get_extra_info('peername')

        # Extract socket ID
        this_socket = transport.get_extra_info('socket')
        self._sock_id = this_socket.fileno()
        local_data = this_socket.getsockname()

        self._logger.info('[%s] local %s port %s connected to %s port %s',
                          self._sock_id, local_data[0], local_data[1],
                          peer_data[0], peer_data[1])

        # No delay OFF -> Nagle's alg used
        this_socket.setsockopt(
            socket.IPPROTO_TCP,
            socket.TCP_NODELAY,
            0)

        # If required - turn off Nagle's alg (No Delay ON)
        if self._no_delay:
            this_socket.setsockopt(
                socket.IPPROTO_TCP,
                socket.TCP_NODELAY,
                1)

        # Set Socket TX/RX buffer sizes if specified
        if self._window:
            self._logger.debug('Setting socket buffer sizes to %s B', self._window)
            this_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self._window)
            this_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self._window)

        # Print current buf sizes:
        rx_buf = this_socket.getsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF)
        tx_buf = this_socket.getsockopt(
                socket.SOL_SOCKET,
                socket.SO_SNDBUF)

        self._logger.debug('Socket TX buffer: %s B; RX buffer: %s B;',
                           tx_buf, rx_buf) 

        self._stream.connection_established(self)

    def data_received(self, data):
        #self._logger.debug('Received %s bytes', len(data))
        self._stream.data_received(data)

    def connection_lost(self, exc):
        self._logger.debug('[%s] Connection lost!', self._sock_id, exc_info=exc)

    def send_data(self, data):
        self._transport.write(data)
