"""
An entry point and a shell holding tests in the iPerf3 server.
"""

import logging
import asyncio
import socket

from py3iperf3.iperf3_test import Iperf3Test
from py3iperf3.tcp_test_protocol import TcpTestProtocol
from py3iperf3.test_settings import TestSettings
from py3iperf3.iperf3_api import COOKIE_SIZE

class Iperf3Server(object):
    """Big ToDo"""

    def __init__(self, parameters, loop=None, use_processes=False):
        """Initialize the server"""

        if loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = loop

        self._use_processes = use_processes
        self._logger = logging.getLogger('py3iperf3')

        self._parameters = TestSettings()
        for attr, value in parameters.items():
            # Set default if Not given
            if value is not None:
                setattr(self._parameters, attr, value)

        self._server = None
        self._orphans = {} # Orphan -> Rxdata
        self._tests = {} # Cookie -> Test

    def start_server(self):
        """Start listening sockets and wait for connections"""

        # Bind on
        if self._parameters.server_address is not '':
            local_addr = self._options.server_address
        else:
            if self._parameters.ip_version == 4:
                local_addr = '0.0.0.0'
            else:
                local_addr = '::'

        # IP Version
        if self._parameters.ip_version == 4:
            ip_ver = socket.AF_INET
        else:
            ip_ver = socket.AF_INET6

        self._logger.info('Binding on %s port %s',
                          local_addr, self._parameters.server_port)

        coro = self._server = self._loop.create_server(
            lambda: TcpTestProtocol(server=self),
            host=local_addr,
            port=self._parameters.server_port,
            family=ip_ver,
            reuse_address=True)
        self._server = self._loop.run_until_complete(coro)
        self._logger.info('Server running!')

    def tcp_connection_established(self, proto):
        """Handle a new TCP conncetion that can be meant for control or data"""

        # Add to orphan list
        self._orphans[proto] = []

    def control_data_received(self, proto, data):
        """Handle data from orphaned connection"""
        
        # Add data to receive buffer
        self._orphans[proto].extend(data)

        # Did we get the cookie?
        if len(self._orphans[proto]) == COOKIE_SIZE+1:
            self.process_proto_with_cookie(proto)

    def process_proto_with_cookie(self, proto):
        """Process connection once cookie is received"""

        cookie = self._orphans[proto]
        cookie_string = bytes(cookie[:-1]).decode('ascii')
        self._logger.debug('Connection: %s Cookie: %s', proto, cookie_string)

        if cookie_string in self._tests:
            # This is data connection for the already existing test
            self._tests[cookie_string].new_data_connection(proto)

        else:
            # This is a fresh cookie. Create a new test
            test = Iperf3Test(self, self._loop, {})
            self._tests[cookie_string] = test
            test.set_control_connection(proto, cookie_string)
            del self._orphans[proto]

    def stop_server(self):
        """Cancel all running tests and stop the server"""
        self._logger.info('Server closing')
        self._server.close()
