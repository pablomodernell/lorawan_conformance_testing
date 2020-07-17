"""
This Module define the main services of the Test Session Coordinator in charge of the testing session.
"""
#################################################################################
# MIT License
#
# Copyright (c) 2018, Pablo D. Modernell, Universitat Oberta de Catalunya (UOC).
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#################################################################################
import json

import lorawan.sessions as device_sessions
import lorawan.parsing.configuration as configuration_parser
import message_queueing
import conformance_testing.test_errors as test_errors
from user_interface.ui import ui_publisher
import user_interface.ui_reports as ui_reports
import parameters.message_broker as message_broker
from parameters.message_broker import routing_keys


class TestSessionCoordinator(message_queueing.MqInterface):
    """
    This class implements the testing service and is in charge of coordinating the execution
    of the selected tests. It is a MqInterface, it can communicate with the RMQ broker in order to receive uplink
    messages and send downlink messages to the agent (using the correct routing key).
    """

    def __init__(self):
        """
        The constructor initializes the downlink counter of the test session (defined in the test application
        protocol) and declares logging queues in the RMQ Broker to avoid the message loss (in case that the clients
        haven't initialized the logging queues when the session starts.
        """
        super().__init__()
        self.device_under_test = None
        self.current_test = None
        self.requested_tests = None
        self._next_test_index = 0
        self._reset_dut = False
        self.downlink_counter = 0
        self.testingtool_on = True
        self.last_deviceid = None

        # >> Declare log queue to avoid message loss --------------------------------------
        self.declare_queue(queue_name='logger_tas', auto_delete=True, exclusive=False)
        log_tas_routing_key = "log." + message_broker.service_names.test_session_coordinator
        self.bind_queue(queue_name='logger_tas', routing_key=log_tas_routing_key)

        self.declare_queue(queue_name='logger_all', auto_delete=True, exclusive=False)
        log_all_routing_key = "log.#"
        self.bind_queue(queue_name='logger_all', routing_key=log_all_routing_key)
        # << End declare log queue  -------------------------------------------------------
        self.declare_queue(queue_name='display_gui', auto_delete=False, exclusive=False)
        self.bind_queue(queue_name='display_gui',
                        routing_key=message_broker.routing_keys.ui_all_users + '.display')
        self.declare_queue(queue_name='configuration_request', auto_delete=False, exclusive=False)
        self.bind_queue(queue_name='configuration_request',
                        routing_key=message_broker.routing_keys.configuration_request)
        self.declare_queue(queue_name='request_action_gui', auto_delete=False, exclusive=False)
        self.bind_queue(queue_name='request_action_gui',
                        routing_key=message_broker.routing_keys.ui_all_users + '.request')

    @property
    def reset_dut(self):
        """ Indicates that the test needs to reset the Device Under Test (DUT) to set it to a known state."""
        return self._reset_dut

    @reset_dut.setter
    def reset_dut(self, reset_value):
        """ Indicates that the test needs to reset the Device Under Test (DUT) to set it to a known state."""
        if reset_value is True:
            self._reset_dut = True
        else:
            self._reset_dut = False
        self.downlink_counter = 0

    def test_available(self):
        """ Returns True if there is a new tests to be executed."""
        return self.requested_tests and self._next_test_index < len(self.requested_tests)

    def pop_next_test_name(self):
        """ Returns the name of the next test to be executed."""
        if self.test_available():
            if self.reset_dut:
                self.reset_dut = False
                return "td_lorawan_reset"
            else:
                idx = self._next_test_index
                self._next_test_index += 1
                return self.requested_tests[idx]

    def publish(self, msg, routing_key, exchange_name=message_queueing.DEFAULT_EXCHANGE):
        """
        Sends a message to the broker using the default channel.
        :param msg: byte sequence of the message to be sent.
        :param routing_key:
        :param exchange_name:
        :return:
        """
        if self.current_test and routing_keys.toAgent in routing_key:
            self.downlink_counter += 1
        super().publish(msg, routing_key)

    def wait_press_start(self):
        """ Publishes the Start button in the GUI."""
        ui_publisher.testingtool_log(msg_str="Showing start button.",
                                     key_prefix=message_broker.service_names.test_session_coordinator)
        start_request_body = ui_reports.InputFormBody(title="Start LoRaWAN testing tool")
        start_request_body.add_field(ui_reports.ButtonInputField(name="START", value=1))
        request_start = ui_reports.RPCRequest(request_key=routing_keys.ui_all_users + '.request',
                                              channel=self.channel,
                                              body=str(start_request_body))

        start_reply_json = request_start.wait_response(timeout_seconds=120).decode()
        self.consume_stop()

    def start_testing(self):
        """ Starts the current test."""
        self.declare_and_consume(queue_name='testingtool_terminate_tas',
                                 routing_key=routing_keys.testing_terminate,
                                 callback=self.session_terminate_handler)
        ui_publisher.testingtool_log(msg_str="Starting current test case...",
                                     key_prefix=message_broker.service_names.test_session_coordinator)
        self.current_test.start_test()

    def session_terminate_handler(self, ch, method, properties, body):
        """ Handles a Sesstion Termination message."""
        ui_publisher.testingtool_log(msg_str="SESSION TERMINATED BY THE USER.",
                                     key_prefix=message_broker.service_names.test_session_coordinator)
        self.consume_stop()
        self.testingtool_on = False
        raise test_errors.SessionTerminatedError("Terminated by UI request.")

    def get_device_from_gui(self):
        """ Requests and validates the Device information using the GUI."""

        class InvalidHexStringInFieldError(Exception):
            pass

        def validate_bytes(number_of_bytes, field_str):
            try:
                field_bytes = bytes.fromhex(field_str)
                if len(field_bytes) == number_of_bytes:
                    return field_bytes
                else:
                    raise InvalidHexStringInFieldError(
                        'The field ({0}) must be {1} bytes long.'.format(
                            field_str,
                            number_of_bytes)
                    )
            except ValueError:
                raise InvalidHexStringInFieldError('{} is an invalid field'.format(field_str))

        ####################################################################################################
        while "The user doesn't enter a valid device information":
            try:
                device_id = configuration_parser.DeviceID()

                device_request_body = ui_reports.InputFormBody(title="Enter device information.")
                device_request_body.add_field(ui_reports.TextInputField(name="DevEUI",
                                                                        label="Device EUI",
                                                                        value="0004a30b001adbe5"))
                device_request_body.add_field(ui_reports.TextInputField(name="AppKey",
                                                                        label="Application Key",
                                                                        value='2b7e151628aed2a6abf7158809cf4f3c'))
                device_request_body.add_field(ui_reports.TextInputField(name="DevAddr",
                                                                        label="Short address",
                                                                        value="26011cf1"))
                ui_publisher.testingtool_log(
                    msg_str="Requesting device credentials: {}.".format(str(device_request_body)),
                    key_prefix=message_broker.service_names.test_session_coordinator)
                request_device = ui_reports.RPCRequest(
                    request_key=routing_keys.ui_all_users + '.request',
                    channel=self.channel,
                    body=str(device_request_body))

                device_reply = device_request_body.get_parsed_reply(
                    request_device.wait_response(timeout_seconds=120))

                device_id.deveui = validate_bytes(number_of_bytes=8,
                                                  field_str=device_reply["DevEUI"])
                device_id.appkey = validate_bytes(number_of_bytes=16,
                                                  field_str=device_reply["AppKey"])
                device_id.devaddr = validate_bytes(number_of_bytes=4,
                                                   field_str=device_reply["DevAddr"])
                device_id.appskey = device_id.appkey
                device_id.nwkskey = device_id.appkey
            except InvalidHexStringInFieldError:
                continue
            else:
                break
        device_display = ui_reports.InputFormBody(title="Device Personalization Information.",
                                                  tag_key="Configuration",
                                                  tag_value="Information")
        device_display.add_field(ui_reports.ParagraphField(
            name=" ",
            value=device_id.to_print_str()))
        ui_publisher.display_on_gui(msg_str=str(device_display),
                                    key_prefix=message_broker.service_names.test_session_coordinator)
        return device_id

    def get_testcases(self):
        """ Request the list of test cases to be run by the test application server. A text box will be displayed
            in the GUI.
        """
        testcases_request_body = ui_reports.InputFormBody(title="List of test cases.")
        testnames_template = ""

        testcases_request_body.add_field(ui_reports.TextInputField(
            name="TestCases",
            label="test cases",
            value=testnames_template))
        request_testcases = ui_reports.RPCRequest(
            request_key=routing_keys.ui_all_users + '.request',
            channel=self.channel,
            body=str(testcases_request_body))
        device_reply = testcases_request_body.get_parsed_reply(
            request_testcases.wait_response(timeout_seconds=120))
        return device_reply["TestCases"].split()

    def ask_configuration_register_device(self):
        """ Use the GUI to request the configuration parameters of the test session:
            -List of testcases
            -DUT personalization parameters
        """
        self.channel.start_consuming()
        ui_publisher.testingtool_log(msg_str="Asking the GUI for configuration.",
                                     key_prefix=message_broker.service_names.test_session_coordinator)

        request_config = ui_reports.RPCRequest(request_key=routing_keys.configuration_request,
                                               channel=self.channel,
                                               body='{"_api_version": "1.0.0"}')
        session_configuration_bytes = request_config.wait_response(timeout_seconds=10)
        ui_publisher.testingtool_log(msg_str="Received configuration from GUI: \n{}".format(
            json.dumps(session_configuration_bytes.decode(), indent=4, sort_keys=True)),
            key_prefix=message_broker.service_names.test_session_coordinator)

        config = ui_reports.SessionConfigurationBody.build_from_json(
            json_str=session_configuration_bytes.decode())

        self.requested_tests = ["td_lorawan_act_01"]
        if config.testcases:
            self.requested_tests.extend(config.testcases)
        else:
            self.requested_tests.extend(self.get_testcases())
        self.requested_tests.append("td_lorawan_deactivate")
        testcases_display = ui_reports.InputFormBody(title="Test Cases to be excecuted.",
                                                     tag_key="Configuration",
                                                     tag_value="Information")
        testcases_display.add_field(ui_reports.ParagraphField(
            name="TCs list:",
            value="\n".join(self.requested_tests)))
        ui_publisher.display_on_gui(msg_str=str(testcases_display),
                                    key_prefix=message_broker.service_names.test_session_coordinator)
        device_id = self.get_device_from_gui()
        ####################################################################################################
        self.device_under_test = device_sessions.EndDevice(ctx_test_tool_service=self,
                                                           deveui=device_id.deveui,
                                                           devaddr=device_id.devaddr,
                                                           appkey=device_id.appkey,
                                                           nwkskey=device_id.nwkskey,
                                                           appskey=device_id.appskey)
        self.last_deviceid = device_id

    def handle_error(self, raised_exception, test_name, result_report=None):
        """ Handles a raised exception, setting a flag to reset the DUT in case of a test failure"""
        error_name = type(raised_exception).__name__
        error_details = str(raised_exception)
        if isinstance(raised_exception, test_errors.TestFailError):
            self.reset_dut = True
        fail_message = "\nTest {0} failed with {1} error.".format(test_name,
                                                                  error_name)
        fail_message_paragraph = ui_reports.ParagraphField(name=test_name, value=fail_message)
        fail_details_paragraph = ui_reports.ParagraphField(name="Details:", value=error_details)
        if result_report:
            result_report.add_field(fail_message_paragraph)
            result_report.add_field(fail_details_paragraph)
            result_report.level = ui_reports.LEVEL_ERR
        step_error = ui_reports.InputFormBody(
            title="{TC}: Step Fail".format(TC=test_name),
            tag_key=test_name,
            tag_value=" ")
        step_error.add_field(fail_message_paragraph)
        step_error.add_field(fail_details_paragraph)
        step_error.level = ui_reports.LEVEL_ERR
        ui_publisher.display_on_gui(msg_str=str(step_error),
                                    key_prefix=message_broker.service_names.test_session_coordinator)
