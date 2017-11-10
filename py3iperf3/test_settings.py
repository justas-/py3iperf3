"""
Default run settings
"""

class TestSettings(object):
    """Default settings of a test"""

    test_protocol = 'T'
    server_address = ''
    server_port = 0

    client_address = None
    client_port = None

    test_duration = 10
    report_interval = 1
    no_delay = False
    parallel = 1
    reverse = False
    title = None
