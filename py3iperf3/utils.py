import random
import string

from py3iperf3.iperf3_api import COOKIE_SIZE

def make_cookie():
    """Make a test cookie"""

    alphabet = string.ascii_letters + string.digits
    cookie = ''

    for _ in range(COOKIE_SIZE):
        cookie += random.choice(alphabet)

    cookie += '\0'

    return cookie
