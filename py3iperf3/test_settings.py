"""
Default run settings
"""

from py3iperf3.iperf3_api import Iperf3TestProto

class TestSettings(object):
    """Default settings of a test"""

    test_protocol = Iperf3TestProto.TCP
    server_address = ''
    server_port = 0

    client_address = None
    client_port = None
    block_size = None
    ip_version = None
    test_duration = 10
    report_interval = 1
    no_delay = False
    parallel = 1
    reverse = False
    title = None
    format = None
    blockcount = None
    bytes = None
