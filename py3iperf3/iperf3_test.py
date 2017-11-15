"""
A class representing a single iPerf3 test on both client and the server.
"""
import logging
import asyncio
import socket
import struct
import json
import time

from py3iperf3.control_protocol import ControlProtocol
from py3iperf3.utils import make_cookie, data_size_formatter
from py3iperf3.iperf3_api import Iperf3State, Iperf3TestProto
from py3iperf3.iperf3_api import DEFAULT_BLOCK_TCP, DEFAULT_BLOCK_UDP
from py3iperf3.test_stream import TestStream
from py3iperf3.error import IPerf3Exception
from py3iperf3.test_settings import TestSettings

class Iperf3Test(object):
    """description of class"""

    def __init__(self, master, loop, test_parameters):
        """ """
        self._master = master   # Ref to Client or Server
        self._loop = loop
        self._parameters = TestSettings()
        self._logger = logging.getLogger('py3iperf3')

        self._streams = []
        self._interval_stats = []

        # Event handles
        self._hdl_stop_test = None
        self._hdl_omitting = None
        self._hdl_stats = None

        self._role = 'c'                # Default role is 'c'-lient, other 's'-server
        self._cookie = None
        self._control_protocol = None
        self._state = None
        self._remote_results = None

        self._test_stopper = 't'        # 't' - time; 'b' - blocks; 's' - data size
        self._blocks_remaining = None
        self._bytes_remaining = None
        self._depleted_called = False

        self._last_stat_collect_time = None
        self._stream_start_time = None

        # Length prefixed strings reception
        self._string_drain = False
        self._string_length = None
        self._string_buffer = bytearray()

        # Overwrite defaults with given params
        self._set_test_parameters(test_parameters)

    @property
    def role(self):
        """Get test role"""
        return self._role

    @property
    def sender(self):
        return not self._parameters.reverse

    @property
    def remote_results(self):
        """Get results received from remote peer"""
        return self._remote_results

    @property
    def role(self):
        return self._role

    @property
    def cookie(self):
        if self._cookie is None:
            self._cookie = make_cookie()

        return self._cookie

    @property
    def server_address(self):
        return self._parameters.server_address

    @property
    def server_port(self):
        return self._parameters.server_port

    @property
    def data_protocol(self):
        return self._parameters.test_protocol

    @property
    def block_size(self):
        return self._parameters.block_size

    @property
    def test_type(self):
        # What stops the test (time/tx blocks/tx data)
        return self._test_stopper

    @property
    def file(self):
        """Get the read/write file"""
        return self._parameters.file

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
        self._control_protocol.send_data(
            self.cookie.encode('ascii'))

    def handle_server_message(self, message):
        """Handle message received from the control socket"""

        # Special handling of length prefixed strings
        if self._string_drain:
            self._drain_to_string(message)
            return

        if len(message) == 1:
            op_codes = struct.unpack('>B', message)
            self._logger.debug("codes: %s", op_codes)
        elif len(message) == 2:
            op_codes = struct.unpack('>BB', message)
            self._logger.debug("codes: %s", op_codes)
        else:
            raise IPerf3Exception('Whoopsy Daisy too many op-codes from the server!')

        for op_code in op_codes:
            self._logger.debug('Op code: %s', op_code)
            state = Iperf3State(op_code)
            self._logger.debug('Received %s state from server', state)
            self._state = state

            if self._state == Iperf3State.PARAM_EXCHANGE:
                # Exchange params
                self._exchange_parameters()

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

                if not self._parameters.reverse:
                    for stream in self._streams:
                        stream.start_stream()

                self._stream_start_time = time.time()

                if self._test_stopper == 't':
                    self._hdl_stop_test = self._loop.call_later(
                        self._parameters.test_duration,
                        self._stop_all_streams)

                self._hdl_stats = self._loop.call_later(
                    self._parameters.report_interval,
                    self._collect_print_stats)

            elif self._state == Iperf3State.TEST_RUNNING:
                self._logger.info('Test is running!')
            elif self._state == Iperf3State.EXCHANGE_RESULTS:
                self._send_results()
                self._string_drain = True # Expect string reply from the server

            elif self._state == Iperf3State.DISPLAY_RESULTS:
                self._logger.info('Received results: %s', self.remote_results)
                self._client_cleanup()
            elif self._state == Iperf3State.IPERF_DONE:
                pass
            elif self._state == Iperf3State.SERVER_TERMINATE:
                pass
            elif self._state == Iperf3State.ACCESS_DENIED:
                raise IPerf3Exception('Access Denied')
            elif self._state == Iperf3State.SERVER_ERROR:
                pass
            else:
                self._logger.debug('Unknown state ID received')

    def sendable_data_depleted(self):
        """Called when blockcount is set and no more blocks remain"""
        # This could be implemented via the get/set property

        if self._depleted_called:
            return

        self._depleted_called = True
        self._stop_all_streams()

    def _collect_print_stats(self):
        """Collect and print periodic statistics"""

        all_stream_stats = []
        t_now = time.time()

        if self._last_stat_collect_time is None:
            scratch_start = 0
        else:
            scratch_start = self._last_stat_collect_time - self._stream_start_time

        scratch_end = t_now - self._stream_start_time
        scratch_seconds = t_now - self._stream_start_time - scratch_start

        self._last_stat_collect_time = t_now

        for stream in self._streams:
            stream_stats = stream.get_stream_interval_stats()
            stream_stats['start'] = scratch_start
            stream_stats['end'] = scratch_end
            stream_stats['seconds'] = scratch_seconds
            stream_stats['bits_per_second'] = stream_stats['bytes'] * 8 / stream_stats['seconds']

            all_stream_stats.append(stream_stats)

        sum_stats = {
            "start":            scratch_start,
			"end":	            scratch_end,
			"seconds":	        scratch_seconds,
			"bytes":	        sum([x['bytes'] for x in all_stream_stats]),
			"bits_per_second":  sum([x['bits_per_second'] for x in all_stream_stats]),
			"retransmits":	    sum([x['retransmits'] for x in all_stream_stats]),
			"omitted":	        False
        }

        stat_ob = {
            "streams" : all_stream_stats,
            "sum" : sum_stats
        }

        self._interval_stats.append(stat_ob)

        if self._parameters.format is None:
            # Autosizing
            speed_str = data_size_formatter(
                int(sum_stats['bits_per_second']), True, False)
        else:
            # Use specific format
            speed_str = data_size_formatter(
                int(sum_stats['bits_per_second']), None, None, self._parameters.format)

        self._logger.info('From: {:.2f} To: {:.2f} Speed: {}/sec'.format(
            scratch_start, scratch_end, speed_str))

        self._hdl_stats = self._loop.call_later(
            self._parameters.report_interval,
            self._collect_print_stats)

    def _client_cleanup(self):
        # close all streams

        # Graceful bye-bye to the server
        self._set_and_send_state(Iperf3State.IPERF_DONE)

        # close control socket
        self._control_protocol.close_connection()

        # Inform master that we are done!
        self._master.test_done(self)

    def _drain_to_string(self, message):

        if self._string_length is None:
            # Drain to buffer until we have at least 4 bytes
            self._string_buffer.extend(message)

            # Return if still not enough data:
            if len(self._string_buffer) < 4:
                return
            else:
                # Parse string length
                self._string_length = struct.unpack('!I', self._string_buffer[:4])[0]
                self._string_buffer = self._string_buffer[4:]
        else:
            self._string_buffer.extend(message)

        # Keep draining until we have enough data
        if len(self._string_buffer) < self._string_length:
            return

        # Decode the string
        string_bytes = self._string_buffer[:self._string_length]
        received_string = string_bytes.decode('ascii')

        # Cleanup
        scratch = self._string_buffer[self._string_length:]
        self._string_length = None
        self._string_buffer = bytearray()
        self._string_drain = False

        self._logger.debug('String draining done!')
        self._save_received_results(received_string)

        # If anything extra is left - process as normal
        if scratch:
            self.handle_server_message(scratch)

    def _save_received_results(self, result_string):
        """Save results string from the server"""

        result_obj = json.loads(result_string)
        self._remote_results = result_obj

    def _send_results(self):
        """Send test results to remote peer"""

        results_obj = {}

        results_obj["cpu_util_total"] = 0
        results_obj["cpu_util_user"] = 0
        results_obj["cpu_util_system"] = 0

        results_obj["sender_has_retransmits"] = 0
        results_obj["congestion_used"] = "Unknown"
        results_obj["streams"] = []

        for stream in self._streams:
            stream_stat_obj = {}

            stream_stat_obj["id"] = 1
            stream_stat_obj["bytes"] = 1
            stream_stat_obj["retransmits"] = 1
            stream_stat_obj["jitter"] = 1
            stream_stat_obj["errors"] = 1
            stream_stat_obj["packets"] = 1
            stream_stat_obj["start_time"] = 1
            stream_stat_obj["end_time"] = 1

            results_obj["streams"].append(stream_stat_obj)

        json_string = json.dumps(results_obj)
        self._logger.debug('Client stats JSON string: %s', json_string)

        len_bytes = struct.pack('!i', len(json_string))
        self._control_protocol.send_data(len_bytes)
        self._control_protocol.send_data(json_string.encode('ascii'))

    def _stop_all_streams(self):

        self._logger.debug('Stopping all streams!')

        for stream in self._streams:
            stream.stop_stream()

        self._set_and_send_state(Iperf3State.TEST_END)

    def _set_and_send_state(self, state):
        """Set test state and send op_code"""

        self._logger.debug('Set and send state: %s', state)

        self._state = state
        self._control_protocol.send_data(
            struct.pack('!c', bytes([state.value])))

    def _set_test_parameters(self, test_parameters):
        """Set test parameters"""

        for attr, value in test_parameters.items():
            setattr(self._parameters, attr, value)

        if self._parameters.block_size is None:
            if self._parameters.test_protocol == Iperf3TestProto.TCP:
                self._parameters.block_size = DEFAULT_BLOCK_TCP
            elif self._parameters.test_protocol == Iperf3TestProto.UDP:
                self._parameters.block_size = DEFAULT_BLOCK_UDP
            else:
                self._parameters.block_size = 1000

        # Remaining time counter
        if self._parameters.test_duration:
            self._test_stopper = 't'

        # Remaining blocks counter
        if self._parameters.blockcount:
            self._blocks_remaining = self._parameters.blockcount
            self._test_stopper = 'b'

        # Remaining bytes counter
        if self._parameters.bytes:
            self._bytes_remaining = self._parameters.bytes
            self._test_stopper = 's'

    def _create_streams(self):
        """Create test streams"""

        try:
            for _ in range(self._parameters.parallel):
                test_stream = TestStream(loop=self._loop, test=self)
                test_stream.create_connection()
                self._streams.append(test_stream)
        except OSError as exc:
            self._logger.exception('Failed creating stream!', exc_info=exc)
            raise IPerf3Exception('Failed to create test stream!')

    def _exchange_parameters(self):
        """Send test parameters to the server"""

        param_obj = {}
        param_obj['tcp'] = True
        param_obj['omit'] = 0
        param_obj['time'] = self._parameters.test_duration
        if self._parameters.bytes:
            param_obj['num'] = self._parameters.bytes
        if self._parameters.blockcount:
            param_obj['blockcount'] = self._parameters.blockcount
        #param_obj['MSS'] = 1400
        #param_obj['nodelay'] = True
        param_obj['parallel'] = self._parameters.parallel
        if self._parameters.reverse:
            param_obj['reverse'] = True
        #param_obj['window'] = 1
        param_obj['len'] = self._parameters.block_size
        #param_obj['bandwidth'] = 1
        #param_obj['fqrate'] = 1
        #param_obj['pacing_timer'] = 1
        #param_obj['burst'] = 1
        #param_obj['TOS'] = 1
        #param_obj['flowlabel'] = 1
        if self._parameters.title:
            param_obj['title'] = self._parameters.title
        #param_obj['congestion'] = ''
        #param_obj['congestion_used'] = ''
        #param_obj['get_server_output'] = 1
        #param_obj['udp_counters_64bit'] = 1
        #param_obj['authtoken'] = ''
        param_obj['client_version'] = 'py3iPerf3_v0.9'

        json_str = json.dumps(param_obj)
        self._logger.debug('Settings JSON (%s): %s',
                      len(json_str), json_str)

        len_bytes = struct.pack('!i', len(json_str))
        self._control_protocol.send_data(len_bytes)
        str_bytes = json_str.encode('ascii')
        self._control_protocol.send_data(str_bytes)

    def _connect_to_server(self):
        """Make a control connection to the server"""

        self._logger.info('Connecting to server %s:%s',
                     self._parameters.server_address,
                     self._parameters.server_port)

        # Connect to
        connect_params = {
            'host' : self._parameters.server_address,
            'port' : self._parameters.server_port
        }

        # Bind on
        if (self._parameters.client_address is not None or
            self._parameters.client_port is not None):

            if self._parameters.client_address is None:
                if (self._parameters.ip_version is not None and
                    self._parameters.ip_version == 6):

                    local_addr = '::'
                else:
                    local_addr = '0.0.0.0'

            else:
                local_addr = self._parameters.client_address

            if self._parameters.client_port is None:
                local_port = 0
            else:
                local_port = self._parameters.client_port

            connect_params['local_addr'] = (local_addr, local_port)

        # IP Version
        if (self._parameters.ip_version is not None and
            self._parameters.ip_version == 4):

            connect_params['family'] = socket.AF_INET

        elif (self._parameters.ip_version is not None and
              self._parameters.ip_version == 6):

            connect_params['family'] = socket.AF_INET6

        self._logger.debug('Connect params: %s', connect_params)

        # Try to connect
        num_retries = 1
        while num_retries > 0:
            try:
                control_connect_coro = self._loop.create_connection(
                    lambda: ControlProtocol(self),
                    **connect_params)
                self._loop.create_task(control_connect_coro)
                break
            except Exception as exc:
                self._logger.exception('Exception connecting to the server!', exc_info=exc)
                time.sleep(1)
                num_retries -= 1

        if num_retries == 0:
            self._logger.error('Failed to connect to the server!')
            return -1
