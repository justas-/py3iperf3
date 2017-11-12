"""
Various utility functions
"""
import math
import random
import string
import logging
import os

from py3iperf3.iperf3_api import COOKIE_SIZE

def make_cookie():
    """Make a test cookie"""

    alphabet = string.ascii_letters + string.digits
    cookie = ''

    for _ in range(COOKIE_SIZE):
        cookie += random.choice(alphabet)

    cookie += '\0'

    return cookie

def setup_logging(debug=False, log_filename=None, **kwargs):
    """Setup logging infrastructure"""

    logger = logging.getLogger('py3iperf3')
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    log_formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)

    logger.addHandler(stream_handler)

    if log_filename is not None:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

def data_size_formatter(size_in_bits, decimal = False, bytes = False):
    """Format size in bits to required dimmension"""

    if size_in_bits < 0:
        # Error?
        return data_size_formatter(-size_in_bits)

    if size_in_bits == 0:
        return '0 bit'

    #TODO: Needs some love!
    dec_bit = ['bit', 'Kib', 'Mib', 'Gib', 'Tib', 'Pib']
    dec_byte = ['Byte', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    bin_bit = ['bit', 'kbit', 'mbit', 'gbit', 'tbit', 'pbit']
    bin_byte = ['Byte', 'KByte', 'MByte', 'GByte', 'TByte', 'PByte']

    if decimal:
        # Decimal format
        postfix = dec_bit
        size_val = size_in_bits

        if bytes:
            size_val = size_in_bits / 8
            postfix = dec_byte

        size_index = min([len(postfix)-1, int(math.floor(math.log10(size_val)/3))])
        digit_string = '{:.2f}'.format(size_val / 10**(3 * size_index))

    else:
        # Binary format
        postfix = bin_bit
        size_val = size_in_bits

        if bytes:
            size_val = size_in_bits / 8
            postfix = bin_byte

        size_index = min([len(postfix)-1, int(math.floor(math.log2(size_val)/8))])
        digit_string = '{:.2f}'.format(size_val / 1024**size_index)

    digit_string = digit_string.rstrip('0').rstrip('.') if '.' in digit_string else digit_string
    return '{} {}'.format(digit_string, postfix[size_index])
