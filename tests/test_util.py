"""
Unit-test for util functions
"""
import unittest

from py3iperf3.iperf3_api import COOKIE_SIZE
from py3iperf3.utils import make_cookie

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
