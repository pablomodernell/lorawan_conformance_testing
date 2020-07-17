"""
This modules defines the basic components of all conformance test, and is independent of the
particular technology under test (e.g. LoRaWAN).
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
import abc
import conformance_testing.test_errors as test_errors
import utils
from user_interface.ui import ui_publisher
import user_interface.ui_reports as ui_reports
import parameters.message_broker as message_broker
from parameters.message_broker import routing_keys
from conformance_testing.testingtool_messages import TestingToolMessage


class Step(object, metaclass=abc.ABCMeta):
    """
    This abstract class represents a step of the test under execution, defining the basic and common
    attributes of all tests, independently of the tested technology. A test is composed of a list of steps and the
    step should be designed to test one specific functionality of the communication standard under test.
    """
    def __init__(self, ctx_test_manager, step_name, next_step=None):
        """Step constructor. The step attribute context_test_session_coordinator is a reference to the Test App Server instance
        of which this step is part.
        """
        self.name = step_name
        self.ctx_test_manager = ctx_test_manager
        self.next_step = next_step
        self.received_testscript_msg = None

    @abc.abstractmethod
    def step_handler(self, ch, method, properties, body):
        """ Handler that processes the received messages."""
        pass

    def basic_check(self, received_testscript_msg_bytes):
        """ Performs a basic check of the messages. Should be Overwritten by the steps that need to perform
         a basic check on every message that arrives from the DUT, as this is called by the Test Manager before
         running the actions of the current step.

        :param received_testscript_msg_bytes: byte sequence of the received message.
        :return: None
        """
        pass

    def send_downlink(self, msg, routing_key):
        ui_publisher.testingtool_log(msg_str=msg,
                                     key_prefix=message_broker.service_names.test_session_coordinator)
        self.ctx_test_manager.ctx_test_session_coordinator.publish(msg=msg,
                                                                   routing_key=routing_key)

    def print_step_info(self, received_str=None, sending=None, additional_message=None):
        """
        Handles the display of the information of the current step, logging, printing on standard output or
        displaying in the GUI the information related to the step of the test under execution.
        :param received_str: Recieved message string.
        :param sending: Message to be sent to the user in this step.
        :param additional_message: Additional message to be presented to the user.
        :return: None
        """
        if not received_str:
            received_str = self.received_testscript_msg.get_printable_str(
                encryption_key=self.ctx_test_manager.device_under_test.loramac_params.appskey)
        step_report = ui_reports.InputFormBody(
            title="{TC}: Step information".format(TC=self.ctx_test_manager.tc_name.upper()),
            tag_key=self.ctx_test_manager.tc_name,
            tag_value=" ")
        if self.next_step:
            step_name = self.next_step.name
        else:
            step_name = "No next step."
        step_info_str = "\nNext step: {NStep}\nReceived from DUT:\n {Rcv}".format(
            NStep=step_name,
            Rcv=received_str)
        step_report.add_field(ui_reports.ParagraphField(name="Completed Step: {}".format(self.name),
                                                        value=""))
        for line in step_info_str.split("\n"):
            step_report.add_field(ui_reports.ParagraphField(name="",
                                                            value=line))
        if sending:
            step_report.add_field(ui_reports.ParagraphField(name="Sending to DUT:",
                                                            value=utils.bytes_to_text(sending)))
        if additional_message:
            step_report.add_field(ui_reports.ParagraphField(name="Additional information:",
                                                            value=additional_message))
        ui_publisher.display_on_gui(msg_str=str(step_report),
                                    key_prefix=message_broker.service_names.test_session_coordinator)

    def success(self):
        """
            Print a success message when the test result is PASS.

            (Step, str) -> (None)

        :return: (None)
        """
        ui_publisher.testingtool_log(msg_str="Test {0}: PASS.\n\n".format(self.ctx_test_manager.tc_name),
                                     key_prefix=message_broker.service_names.test_session_coordinator)
        self.ctx_test_manager.ctx_test_session_coordinator.consume_stop()


class TestManager(object, metaclass=abc.ABCMeta):
    """ The implementation of each Test Case consists of a Test Manager that knows the list of steps to be executed.
    """
    @abc.abstractmethod
    def __init__(self, test_name, ctx_test_session_coordinator):
        """
        :param ctx_test_session_coordinator: test session coordinator of the current test session.
        :param test_name: name of the test.
        """
        self.tc_name = test_name
        self.device_under_test = ctx_test_session_coordinator.device_under_test
        self.ctx_test_session_coordinator = ctx_test_session_coordinator
        self.test_label = ui_reports.InputFormBody(title="TEST CASE: {TC}".format(TC=self.tc_name),
                                                   tag_key=self.tc_name,
                                                   tag_value=" ")
        self.ctx_test_session_coordinator.declare_and_consume(queue_name='up_tas',
                                                              routing_key=routing_keys.fromAgent+'.#',
                                                              callback=self.message_handler)
        ui_publisher.testingtool_log(msg_str="Init Test Manager, starting test: {0}".format(test_name),
                                     key_prefix=message_broker.service_names.test_session_coordinator)

    def get_testcase_str(self):
        """ Returns a string with all the information of the tests to be displayed to the user."""
        return str(self.test_label)

    def add_step_description(self, step_name, description):
        """ Adds a text field in the test case description to be shown in the GUI."""
        description_lines = description.split('\n')
        self.test_label.add_field(ui_reports.ParagraphField(name=step_name, value=""))
        for line in description_lines:
            self.test_label.add_field(ui_reports.ParagraphField(name="", value=line))

    def start_test(self):
        ui_publisher.display_on_gui(msg_str=self.get_testcase_str(),
                                    key_prefix=message_broker.service_names.test_session_coordinator)
        self.ctx_test_session_coordinator.consume_start()

    def go_to_next_step(self):
        if self.current_step.next_step:
            self.current_step = self.current_step.next_step
            self.current_step.ctx_test_manager = self

    def message_handler(self, ch, method, properties, body):
        self.current_step.basic_check(received_testscript_msg_bytes=body)
        self.current_step.step_handler(ch=ch,
                                       method=method,
                                       properties=properties,
                                       body=body)
        self.go_to_next_step()
