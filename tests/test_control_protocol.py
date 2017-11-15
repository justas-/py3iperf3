"""
Unit-test for control protocol between the client and server.
"""
import unittest
import unittest.mock

from py3iperf3.control_protocol import ControlProtocol

class TestControlProtocol(unittest.TestCase):
    """Unit-test of control protocol"""

    @unittest.mock.patch('py3iperf3.utils.logging.getLogger')
    def test_control_init(self, mock_logger):
        """Test correct init of the object"""

        mock_test = unittest.mock.MagicMock()
        control_proto = ControlProtocol(mock_test)

        self.assertIs(control_proto._test, mock_test)
        assert mock_logger.called_with('py3iperf3')

    def test_control_conn_made(self):
        """Test connection made callback actions"""

        mock_test = unittest.mock.MagicMock()
        mock_transport = unittest.mock.MagicMock()
        
        control_proto = ControlProtocol(mock_test)
        control_proto.connection_made(mock_transport)

        self.assertIs(control_proto._transport, mock_transport)
        assert mock_test.server_connection_established.called_with(
            control_proto)

    def test_control_data_rx(self):
        """Test RX data path"""

        mock_test = unittest.mock.MagicMock()
        message = 'FooBar'.encode('ascii')

        control_proto = ControlProtocol(mock_test)
        control_proto.data_received(message)

        assert mock_test.handle_server_message.called_with(
            message)

    def test_control_data_tx(self):
        """Test TX data path"""

        mock_test = unittest.mock.MagicMock()
        mock_transport = unittest.mock.MagicMock()
        message = 'FooBar'

        control_proto = ControlProtocol(mock_test)
        control_proto.connection_made(mock_transport)
        control_proto.send_data(message)

        assert mock_transport.write.called_with(message)

    def test_control_close_connection(self):
        """Test closing of the connection"""

        mock_test = unittest.mock.MagicMock()
        mock_transport = unittest.mock.MagicMock()

        control_proto = ControlProtocol(mock_test)
        control_proto.connection_made(mock_transport)
        control_proto.close_connection()

        self.assertTrue(control_proto._is_closed)
        assert mock_transport.close.called
