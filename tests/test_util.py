import unittest

from py3iperf3.iperf3_api import COOKIE_SIZE
from py3iperf3.utils import make_cookie

class TestUtilFunctions(unittest.TestCase):
    """description of class"""

    def test_cookie_lenght(self):
        cookie = make_cookie()
        self.assertEqual(len(cookie), COOKIE_SIZE+1)

    def test_cookie_null_end(self):
        cookie = make_cookie()
        self.assertEqual(cookie[-1], '\0')
