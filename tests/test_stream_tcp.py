"""
Unittest for TCP data stream
"""
import unittest
import unittest.mock
import socket

from py3iperf3.data_stream_tcp import TestStreamTcp

class TestTcpStream(unittest.TestCase):
    """
    Unit tests for TCP (and base) stream.
    """

    @unittest.mock.patch('py3iperf3.utils.logging.getLogger')
    def test_object_setup(self, mock_logger):
        """
        Test stream (TCP/Base) init.
        """

        mock_loop = unittest.mock.MagicMock()
        mock_test = unittest.mock.MagicMock()
        mock_test.file = None
        params = {
            'loop': mock_loop,
            'test': mock_test,
            'stream_id': 7,
        }

        tcp_stream = TestStreamTcp(**params)

        # Init in non paused state
        self.assertFalse(tcp_stream._paused)

        # Logger accessed
        assert mock_logger.called_with('py3iperf3')

        # Stream ID set
        self.assertEqual(tcp_stream._stream_id, 7)

        # Init in not done state
        self.assertFalse(tcp_stream.done)

        # Loop and test references set
        self.assertIs(tcp_stream._loop, mock_loop)
        self.assertIs(tcp_stream._test, mock_test)

    def test_connection_established(self):
        """
        Test on connection callback actions.
        """

        mock_loop = unittest.mock.MagicMock()
        mock_test = unittest.mock.MagicMock()
        mock_test.cookie = 'cookie'
        mock_test.file = None
        params = {
            'loop': mock_loop,
            'test': mock_test,
            'stream_id': 7,
        }

        tcp_stream = TestStreamTcp(**params)

        mock_proto = unittest.mock.MagicMock()
        tcp_stream.connection_established(mock_proto)

        # Proto is set
        self.assertIs(tcp_stream._test_protocol, mock_proto)
        # Cookie is sent
        assert mock_proto.send_data.called_with('cookie'.encode('ascii'))

    def test_flow_control(self):
        """
        Test flow control functions.
        """

        mock_loop = unittest.mock.MagicMock()
        mock_test = unittest.mock.MagicMock()
        mock_test.file = None
        params = {
            'loop': mock_loop,
            'test': mock_test,
            'stream_id': 7,
        }

        tcp_stream = TestStreamTcp(**params)

        # Pause on pause
        tcp_stream.pause_writing()
        self.assertTrue(tcp_stream._paused)

        # Cancel and clear the sending handle when present
        mock_handle = unittest.mock.MagicMock()
        tcp_stream._sending_handle = mock_handle
        tcp_stream._paused = False

        tcp_stream.pause_writing()
        self.assertTrue(tcp_stream._paused)
        assert mock_handle.cancel.called
        self.assertIsNone(tcp_stream._sending_handle)

        # Resumptio should change state and call try sending
        tcp_stream.resume_writing()
        self.assertFalse(tcp_stream._paused)
        assert mock_loop.call_soon.called_with(tcp_stream._try_sending)
