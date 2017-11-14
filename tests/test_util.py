"""
Unit-test for util functions
"""
import unittest

from py3iperf3.iperf3_api import COOKIE_SIZE
from py3iperf3.utils import make_cookie, data_size_formatter, setup_logging

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

    def test_size_formatter(self):
        """Test correct formatting of size strings"""
        self.assertEqual(
            data_size_formatter(0, True, False),
            '0 bit')
        self.assertEqual(
            data_size_formatter(100, True, False),
            '100 bit')
        self.assertEqual(
            data_size_formatter(1200, True, False),
            '1.2 Kib')
        self.assertEqual(
            data_size_formatter(1220000, True, False),
            '1.22 Mib')
        self.assertEqual(
            data_size_formatter(1226000000, True, False),
            '1.23 Gib')

        self.assertEqual(
            data_size_formatter(800, True, True),
            '100 Byte')

        self.assertEqual(
            data_size_formatter(167654, False, False),
            '163.72 kbit')
        self.assertEqual(
            data_size_formatter(76894335, False, False),
            '73.33 mbit')

        self.assertEqual(
            data_size_formatter(80000, False, True),
            '9.77 KByte')

        # Test negatives:
        self.assertEqual(
            data_size_formatter(-800, True, True),
            '100 Byte')

    def test_exact_formatter(self):
        """Test correct formatter with given prefix"""

        self.assertEqual(
            data_size_formatter(10000, False, False, 'k'),
            '10 Kib')

        self.assertEqual(
            data_size_formatter(80000, False, False, 'K'),
            '10 KiB')

    @unittest.mock.patch('py3iperf3.utils.logging.StreamHandler')
    @unittest.mock.patch('py3iperf3.utils.logging.getLogger')
    @unittest.mock.patch('py3iperf3.utils.logging.FileHandler')
    def test_setup_logging(self, mock_strh, mock_file_handler, mock_logger):
        """Test setting up of the logger"""

        # Debug
        debug = True
        setup_logging(debug, None)
        assert mock_logger.getLogger.called_with('py3iperf3')
        assert mock_logger.setLevel.called_with('logging.DEBUG')

        debug = False
        setup_logging(debug, None)
        assert mock_logger.getLogger.called_with('py3iperf3')
        assert mock_logger.setLevel.called_with('logging.INFO')

        # Stream handler
        assert mock_logger.addHandler.called_with(mock_strh)

        # Log filename
        filename = 'foo.log'
        debug = True
        setup_logging(debug, filename)
        assert mock_file_handler.called_with(filename)
        assert mock_logger.addHandler.called_with(mock_file_handler)
