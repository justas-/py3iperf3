"""
Unit-test for util functions
"""
import unittest

from py3iperf3.iperf3_api import COOKIE_SIZE
from py3iperf3.utils import make_cookie, data_size_formatter

class TestUtilFunctions(unittest.TestCase):
    """Unit-tests of utilities function"""

    def test_cookie_lenght(self):
        """Test correct cookie length"""
        cookie = make_cookie()
        self.assertEqual(len(cookie), COOKIE_SIZE+1)

    def test_cookie_null_end(self):
        """Test cookie is null terminated"""
        cookie = make_cookie()
        self.assertEqual(cookie[-1], '\0')

    def test_size_formatter(self):
        """Test correct formatting of size strings"""
        self.assertEqual(
            data_size_formatter(0, True, False),
            '0 bit')
        self.assertEqual(
            data_size_formatter(100, True, False),
            '100 bit')
        self.assertEqual(
            data_size_formatter(1200, True, False),
            '1.2 Kib')
        self.assertEqual(
            data_size_formatter(1220000, True, False),
            '1.22 Mib')
        self.assertEqual(
            data_size_formatter(1226000000, True, False),
            '1.23 Gib')

        self.assertEqual(
            data_size_formatter(800, True, True),
            '100 Byte')

        self.assertEqual(
            data_size_formatter(167654, False, False),
            '0.16 mbit')