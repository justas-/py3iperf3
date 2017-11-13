"""
Unit-test for Iperf3Test class
"""
#pylint: disable=protected-access, no-member

import random
import struct
import unittest
import unittest.mock

from py3iperf3.iperf3_test import Iperf3Test
from py3iperf3.iperf3_api import Iperf3TestProto, DEFAULT_BLOCK_TCP, DEFAULT_BLOCK_UDP
from py3iperf3.iperf3_api import Iperf3State

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
    def test_cookie_set_on_call(self, _):
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

    def test_server_connection_saved_and_cookie_tx(self):
        """
        Test saving of server control protocol and sending
        of the cookie.
        """

        fake_proto = unittest.mock.MagicMock()

        iperf_test = Iperf3Test(None, None, {})
        cookie_str = iperf_test.cookie

        iperf_test.server_connection_established(fake_proto)

        self.assertIs(iperf_test._control_protocol, fake_proto)
        fake_proto.send_data.assert_called_with(cookie_str.encode('ascii'))

    @unittest.mock.patch('py3iperf3.iperf3_test.TestStream')
    def test_streams_created_destroyed(self, _):
        """Test creation of multiple streams"""

        num_parallel = random.randint(2, 5)
        test_params = {
            'parallel':num_parallel
        }
        mock_proto = unittest.mock.MagicMock()

        iperf_test = Iperf3Test(None, None, test_params)
        iperf_test._control_protocol = mock_proto
        iperf_test.handle_server_message(struct.pack(
            '!c', bytes([Iperf3State.CREATE_STREAMS.value])))

        # Ensure streams created and connect attempted
        self.assertEqual(len(iperf_test._streams), num_parallel)
        for test_stream in iperf_test._streams:
            assert test_stream.create_connection.called

        # Ensure streams are stopped
        iperf_test._stop_all_streams()
        for test_stream in iperf_test._streams:
            assert test_stream.stop_stream.called

    def test_block_size_setting(self):
        """Test various block size settings"""

        # Default TCP:
        iperf_test = Iperf3Test(None, None, {})
        self.assertTrue(iperf_test.block_size, DEFAULT_BLOCK_TCP)

        # Preset size
        test_params = {
            'block_size':31337
        }
        iperf_test = Iperf3Test(None, None, test_params)
        self.assertTrue(iperf_test.block_size, 31337)
