"""
Unit-test for Iperf3Client class
"""
#pylint: disable=protected-access, no-member

import unittest
import unittest.mock

from py3iperf3.iperf3_client import Iperf3Client
from py3iperf3.iperf3_test import Iperf3Test

def fake_get_event_loop():
    """Replacement for asyncio.get_event_loop()"""
    return 'Fake'

class TestIperf3ClientClass(unittest.TestCase):
    """Unit tests of iPerf3 client class"""

    def test_save_given_loop(self):
        """Test for saving the given loop"""

        mock_loop = unittest.mock.Mock()
        client = Iperf3Client(loop=mock_loop)
        self.assertIs(client._loop, mock_loop)

    @unittest.mock.patch('asyncio.get_event_loop',
                         side_effect=fake_get_event_loop)
    def test_use_default_loop(self, _):
        """Test for obtaining the default loop"""

        client = Iperf3Client(loop=None)
        self.assertEqual(client._loop, 'Fake')

    def test_create_test(self):
        """Test the creation of the test"""

        mock_loop = unittest.mock.Mock()
        client = Iperf3Client(loop=mock_loop)
        test = client.create_test(test_parameters={})

        self.assertIsInstance(test, Iperf3Test)
        self.assertIn(test, client._tests)

    @unittest.mock.patch('py3iperf3.iperf3_test.Iperf3Test.run')
    def test_run_all_test(self, _):
        """Test starting of all tests"""

        mock_loop = unittest.mock.Mock()
        client = Iperf3Client(loop=mock_loop)
        test1 = client.create_test(test_parameters={})
        test2 = client.create_test(test_parameters={})

        client.run_all_tests()

        self.assertTrue(test1.run.called)
        self.assertTrue(test2.run.called)

    @unittest.mock.patch('py3iperf3.iperf3_test.Iperf3Test.stop')
    def test_stop_all_test(self, _):
        """Test starting of all tests"""

        mock_loop = unittest.mock.Mock()
        client = Iperf3Client(loop=mock_loop)
        test1 = client.create_test(test_parameters={})
        test2 = client.create_test(test_parameters={})

        client.stop_all_tests()

        self.assertTrue(test1.stop.called)
        self.assertTrue(test2.stop.called)

    @unittest.mock.patch('logging.error')
    def test_process_finished(self, le):
        """Test removal of the finished tests"""

        mock_loop = unittest.mock.Mock()
        client = Iperf3Client(loop=mock_loop)

        mock_test1 = unittest.mock.Mock()
        mock_test2 = unittest.mock.Mock()

        client._tests.extend([mock_test1, mock_test2])

        # Remove the first test
        client.test_done(mock_test1)

        self.assertNotIn(mock_test1, client._tests)
        self.assertFalse(mock_loop.stop.called)

        # Remove the last test
        client.test_done(mock_test2)

        self.assertNotIn(mock_test2, client._tests)
        self.assertTrue(mock_loop.stop.called)

        # Remove non-existing test

        client.test_done(mock_test2)
        self.assertTrue(le.called)
