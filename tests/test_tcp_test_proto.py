"""
Unit-test for the TCP data protocol.
"""
import unittest
import unittest.mock

from py3iperf3.data_protocol_tcp import TcpTestProtocol

def fake_logger(message, **kwargs):
    """Mockup of logger"""
    return unittest.mock.MagicMock()

class TestTcpTestProtocol(unittest.TestCase):
    """Unit-test of TCP data proto"""

    @unittest.mock.patch('py3iperf3.utils.logging.getLogger')
    def test_tcp_proto_init(self, mock_logger):
        """Test correct init of the object"""

        mock_stream = unittest.mock.MagicMock()
        tcp_proto = TcpTestProtocol(mock_stream)

        self.assertIs(tcp_proto._stream, mock_stream)
        assert mock_logger.called_with('py3iperf3')

    def test_tcp_conn_made(self):
        """Test connection made callback actions"""

        mock_transport = unittest.mock.MagicMock() 
        mock_stream = unittest.mock.MagicMock()

        tcp_proto = TcpTestProtocol(mock_stream)
        tcp_proto.connection_made(mock_transport)

        self.assertIs(tcp_proto._transport, mock_transport)
        assert mock_stream.connection_established.called_with(
            tcp_proto)

    def test_tcp_data_rx(self):
        """Test RX data path"""

        mock_stream = unittest.mock.MagicMock()
        message = 'FooBar'.encode('ascii')

        tcp_proto = TcpTestProtocol(mock_stream)
        tcp_proto.data_received(message)

        assert mock_stream.data_received.called_with(
            message)

    def test_tcp_data_tx(self):
        """Test TX data path"""

        mock_stream = unittest.mock.MagicMock()
        mock_transport = unittest.mock.MagicMock()
        message = 'FooBar'

        tcp_proto = TcpTestProtocol(mock_stream)
        tcp_proto.connection_made(mock_transport)
        tcp_proto.send_data(message)

        assert mock_transport.write.called_with(message)

    @unittest.mock.patch('py3iperf3.utils.logging.getLogger',
                         side_effec=fake_logger)
    def test_tcp_data_connection_lost(self, fake_logger):
        """Test logging of connection lost event"""

        mock_stream = unittest.mock.MagicMock()
        mock_stream.done = True

        tcp_proto = TcpTestProtocol(mock_stream)

        # Done stream should not call debug
        tcp_proto.connection_lost(None)
        assert not tcp_proto._logger.debug.called

        # Not done stream should call debug
        mock_stream.done = False
        tcp_proto.connection_lost(None)
        assert tcp_proto._logger.debug.called

    def test_socket_no(self):
        """
        Test setting/getting socket ID
        """
        mock_socket = unittest.mock.MagicMock()
        mock_socket.fileno = unittest.mock.MagicMock(return_value=7)

        mock_transport = unittest.mock.MagicMock()
        mock_transport.get_extra_info = unittest.mock.MagicMock(return_value=mock_socket)

        mock_stream = unittest.mock.MagicMock()

        tcp_proto = TcpTestProtocol(mock_stream)
        tcp_proto.connection_made(mock_transport)

        assert mock_transport.fileno.called_once_with('socket')
        self.assertEqual(tcp_proto.socket_id, 7)
