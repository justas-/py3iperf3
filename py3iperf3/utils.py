"""
Various utility functions
"""
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
