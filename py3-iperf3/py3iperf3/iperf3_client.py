import logging
import asyncio

from py3iperf3.iperf3_test import Iperf3Test

class Iperf3Client(object):
    """Implements iPerf3 Client functionality"""

    def __init__(self, loop=None, use_processes=False):
        """Initialize the client"""
        
        if loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = loop

        self._use_processes = use_processes

        self._tests = []

    def create_test(self, test_parameters):
        """Create and return an instance of a test"""
        
        test = Iperf3Test(
            loop=self._loop,
            test_parameters=test_parameters)
        self._tests.append(test)
        return test

    def run_all_tests(self):
        """Run all tests"""
        
        for test in self._tests:
            test.run()
        
    def stop_all_tests(self):
        """Request all tests to stop"""

        for test in self._tests():
            test.stop()
