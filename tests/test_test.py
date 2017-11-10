"""
Unit-test for Iperf3Test class
"""
#pylint: disable=protected-access, no-member

import unittest
import unittest.mock

from py3iperf3.iperf3_test import Iperf3Test
from py3iperf3.iperf3_api import Iperf3TestProto

def fake_cookie():
    """Fake cookie generator"""
    return 'FooCookie'

class TestIperf3TestClass(unittest.TestCase):
    """Unit tests of iPerf3 test class"""

    def test_save_given_parameters(self):
        """Test for saving master and loop params"""

        fake_master = unittest.mock.MagicMock()
        fake_loop = unittest.mock.MagicMock()

        iperf_test = Iperf3Test(fake_master, fake_loop, {})

        self.assertIs(iperf_test._master, fake_master)
        self.assertIs(iperf_test._loop, fake_loop)

    def test_saving_params_and_iface(self):
        """Test saving of the test parameters"""
        
        fake_master = unittest.mock.MagicMock()
        fake_loop = unittest.mock.MagicMock()
        param_obj = {
            'reverse':True,
            'server_address':'foo.server.local',
            'server_port':1337,
            'test_protocol':Iperf3TestProto.UDP,
            'block_size':31337,
        }

        iperf_test = Iperf3Test(fake_master, fake_loop, param_obj)

        self.assertEqual(iperf_test.sender, False)
        self.assertEqual(iperf_test.server_address, 'foo.server.local')
        self.assertEqual(iperf_test.server_port, 1337)
        self.assertEqual(iperf_test.data_protocol, Iperf3TestProto.UDP)
        self.assertEqual(iperf_test.block_size, 31337)

    @unittest.mock.patch('py3iperf3.iperf3_test.make_cookie',
                         side_effect=fake_cookie)
    def test_cookie_set_on_call(self, fakecookie):
        """Test setting of cookie on the first call"""

        fake_master = unittest.mock.MagicMock()
        fake_loop = unittest.mock.MagicMock()
        param_obj = {}

        iperf_test = Iperf3Test(fake_master, fake_loop, param_obj)

        self.assertIsNone(iperf_test._cookie)
        self.assertEqual(iperf_test.cookie, 'FooCookie')

    def test_cookie_doesnt_change(self):
        """Test consistency of the cookie after multiple accesses"""

        fake_master = unittest.mock.MagicMock()
        fake_loop = unittest.mock.MagicMock()
        param_obj = {}

        iperf_test = Iperf3Test(fake_master, fake_loop, param_obj)
        cookie_str = iperf_test.cookie

        self.assertEqual(iperf_test.cookie, cookie_str)
