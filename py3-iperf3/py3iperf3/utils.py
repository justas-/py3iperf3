import random
import string

COOKIE_SIZE = 36

def make_cookie():
    """Make a test cookie"""

    alphabet = string.ascii_letters + string.digits
    cookie = ''
    
    for _ in range(COOKIE_SIZE):
        cookie += random.choice(alphabet)

    cookie += '\0'
    
    return cookie
