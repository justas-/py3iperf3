"""
Unitttest for the UDP data protocol.
"""
import unittest
import unittest.mock
import socket

from py3iperf3.data_protocol_udp import UdpTestProtocol

class TestUdpTestProtocol(unittest.TestCase):
    """
    Unittest for UDP proto.
    """

    @unittest.mock.patch('py3iperf3.utils.logging.getLogger')
    def test_udp_proto_init(self, mock_logger):
        """
        Test initialization of object.
        """

        mock_stream = unittest.mock.MagicMock()
        udp_proto = UdpTestProtocol(mock_stream)

        # Test that stream is set and logger created
        self.assertIs(udp_proto._stream, mock_stream)
        assert mock_logger.called_with('py3iperf3')

    def test_udp_connection_made(self):
        """
        Test connection made callback.
        """
        mock_socket = unittest.mock.MagicMock()
        mock_socket.fileno = unittest.mock.MagicMock(return_value=7)

        mock_transport = unittest.mock.MagicMock()
        mock_transport.get_extra_info = unittest.mock.MagicMock(return_value=mock_socket)

        mock_stream = unittest.mock.MagicMock()

        udp_proto = UdpTestProtocol(mock_stream)
        udp_proto.connection_made(mock_transport)

        self.assertIs(udp_proto._transport, mock_transport)
        assert mock_transport.get_extra_info.called_with('peername')
        assert mock_transport.get_extra_info.called_with('socket')
        assert mock_socket.fileno.called
        self.assertEqual(udp_proto.socket_id, 7)

    def test_udp_datagram_received(self):
        """
        Test datagram received callback.
        """
        mock_stream = unittest.mock.MagicMock()
        udp_proto = UdpTestProtocol(mock_stream)

        udp_proto.datagram_received('foo', 'bar')
        assert mock_stream.data_received.called_with('foo', 'bar')

    def test_udp_datagram_sending(self):
        """
        Test datagram sending.
        """
        mock_socket = unittest.mock.MagicMock()
        mock_socket.fileno = unittest.mock.MagicMock(return_value=7)

        mock_transport = unittest.mock.MagicMock()
        mock_transport.get_extra_info = unittest.mock.MagicMock(return_value=mock_socket)

        mock_stream = unittest.mock.MagicMock()

        udp_proto = UdpTestProtocol(mock_stream)
        udp_proto.connection_made(mock_transport)
        
        udp_proto.send_data('foo')
        assert mock_transport.sendto.called_with('foo')
