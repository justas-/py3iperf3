import logging
import asyncio
import struct
import json
import time

from py3iperf3.control_protocol import ControlProtocol
from py3iperf3.utils import make_cookie
from py3iperf3.iperf3_api import Iperf3State
from py3iperf3.test_stream import TestStream
from py3iperf3.error import PyiPerf3Exception
from py3iperf3.test_settings import TestSettings

class Iperf3Test(object):
    """description of class"""

    def __init__(self, loop=None, test_parameters=None):
        """ """
        self._loop = loop
        self._parameters = TestSettings()
        self._set_test_parameters(test_parameters)

        # Call-backs
        self._cb_on_connect = []

        self._streams = []

        self._cookie = None
        self._control_protocol = None
        self._state = None

    @property
    def cookie(self):
        return self._cookie

    @property
    def server_address(self):
        return self._parameters.server_address

    @property
    def server_port(self):
        return self._parameters.server_port

    def run(self):
        """Start the test"""

        self._connect_to_server()

    def stop(self):
        """Stop the test"""
        pass

    def server_connection_established(self, control_protocol):
        """Callback on established server connection"""
        self._control_protocol = control_protocol

        # Make and send cookie
        self._cookie = make_cookie()
        self._control_protocol.send_data(
            self._cookie.encode('ascii'))

    def handle_server_message(self, message):
        """Handle message received from the control socket"""

        if len(message) == 1:
            op_codes = struct.unpack('>B', message)
            logging.debug("codes: %s", op_codes)
        elif len(message) == 2:
            op_codes = struct.unpack('>BB', message)
            logging.debug("codes: %s", op_codes)
        else:
            raise PyiPerf3Exception('Whoopsy Daisy too many op-codes from the server!')

        for op_code in op_codes:
            logging.debug('Op code: %s', op_code)
            state = Iperf3State(op_code)
            logging.debug('Received %s state from server', state)
            self._state = state

            if self._state == Iperf3State.PARAM_EXCHANGE:
                # Exchange params
                self._exchange_parameters()

                # Run on_connect callbacks
                for cb_func in self._cb_on_connect:
                    cb_func(self)
            elif self._state == Iperf3State.CREATE_STREAMS:
                # Create required streams
                self._create_streams()
            elif self._state == Iperf3State.TEST_START:
                #if (iperf_init_test(test) < 0)
                #   return -1;
                #if (create_client_timers(test) < 0)
                #   return -1;
                #if (create_client_omit_timer(test) < 0)
                #   return -1;
	            #if (!test->reverse)
		        #   if (iperf_create_send_timers(test) < 0)
		        #       return -1;
                for stream in self._streams:
                    stream.start_stream()

                self._loop.call_later(
                    self._parameters.test_duration,
                    self._stop_all_streams)

            elif self._state == Iperf3State.TEST_RUNNING:
                logging.info('Test is running!')
            elif self._state == Iperf3State.EXCHANGE_RESULTS:
                pass
            elif self._state == Iperf3State.DISPLAY_RESULTS:
                pass
            elif self._state == Iperf3State.IPERF_DONE:
                pass
            elif self._state == Iperf3State.SERVER_TERMINATE:
                pass
            elif self._state == Iperf3State.ACCESS_DENIED:
                raise PyiPerf3Exception('Access Denied')
            elif self._state == Iperf3State.SERVER_ERROR:
                pass
            else:
                logging.debug('Unknown state ID received')

    def _stop_all_streams(self):

        logging.debug('Stopping all streams!')

        for stream in self._streams:
            stream.stop_stream()

        self._set_and_send_state(Iperf3State.TEST_END)

    def _set_and_send_state(self, state):
        """Set test state and send op_code"""

        logging.debug('Set and send state: %s', state)

        self._state = state
        self._control_protocol.send_data(
            struct.pack('!c', bytes([state.value])))

    def _set_test_parameters(self, test_parameters):
        """Set test parameters"""

        for attr, value in test_parameters.items():
            setattr(self._parameters, attr, value)

    def _create_streams(self):
        """Create test streams"""

        for _ in range(self._parameters.parallel):
            test_stream = TestStream(loop=self._loop, test=self)
            test_stream.create_connection()
            self._streams.append(test_stream)

    def _exchange_parameters(self):
        """Send test parameters to the server"""

        param_obj = {}
        param_obj['tcp'] = True
        param_obj['omit'] = 0
        param_obj['time'] = 5
        #param_obj['num'] = 1
        #param_obj['blockcount'] = 1
        #param_obj['MSS'] = 1400
        #param_obj['nodelay'] = True
        param_obj['parallel'] = 1
        #param_obj['reverse'] = True
        #param_obj['window'] = 1
        param_obj['len'] = 131072
        #param_obj['bandwidth'] = 1
        #param_obj['fqrate'] = 1
        #param_obj['pacing_timer'] = 1
        #param_obj['burst'] = 1
        #param_obj['TOS'] = 1
        #param_obj['flowlabel'] = 1
        #param_obj['title'] = 'test'
        #param_obj['congestion'] = ''
        #param_obj['congestion_used'] = ''
        #param_obj['get_server_output'] = 1
        #param_obj['udp_counters_64bit'] = 1
        #param_obj['authtoken'] = ''
        param_obj['client_version'] = 'py3-iPerf3_v0.9'

        json_str = json.dumps(param_obj)
        logging.debug('Settings JSON (%s): %s',
                      len(json_str), json_str)

        len_bytes = struct.pack('!i', len(json_str))
        self._control_protocol.send_data(len_bytes)
        str_bytes = json_str.encode('ascii')
        self._control_protocol.send_data(str_bytes)

    def _connect_to_server(self):
        """Make a control connection to the server"""

        logging.info('Connecting to server %s:%s',
                     self._parameters.server_address,
                     self._parameters.server_port)

        # Try to connect
        num_retries = 1
        while num_retries > 0:
            try:
                control_connect_coro = self._loop.create_connection(
                    lambda: ControlProtocol(self),
                    self._parameters.server_address,
                    self._parameters.server_port)
                self._loop.create_task(control_connect_coro)
                break
            except Exception as exc:
                logging.exception('Exception connecting to the server!', exc_info=exc)
                time.sleep(1)
                num_retries -= 1

        if num_retries == 0:
            logging.error('Failed to connect to the server!')
            return -1
