"""
An entry point and a shell holding tests in the iPerf3 server.
"""
class Iperf3Server(object):
    """Big ToDo"""

    def __init__(self, loop=None, use_processes=False):
        """Initialize the server"""

        if loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = loop

        self._use_processes = use_processes
        self._logger = logging.getLogger('py3iperf3')

        self._tests = []

    def start_server(self):
        """Start listening sockets and wait for connections"""
        pass

    def stop_server(self):
        """Cancel all running tests and stop the server"""
        pass
