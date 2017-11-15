"""
Unit-test for the TCP data protocol.
"""
import unittest
import unittest.mock

from py3iperf3.tcp_test_protocol import TcpTestProtocol

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
