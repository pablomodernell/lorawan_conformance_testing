"""
LoRaWAN Specification v1.0.2
Test Case Group: LoRaWAN
This modules includes all the test Steps that are common to all LoRaWAN test groups.
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
import struct
import utils

import lorawan.sessions
import lorawan.lorawan_parameters.general as general_parameters
import conformance_testing.test_step_sequence
import lorawan.lorawan_conformance.lorawan_errors as lorawan_errors
import conformance_testing.test_errors as test_errors
from lorawan.parsing import flora_messages
import lorawan.lorawan_utils
from user_interface.ui import ui_publisher
import parameters.message_broker as message_broker
import lorawan.parsing.lorawan as lorawan_parser
import lorawan.lorawan_parameters.testing as tests_parameters
import user_interface.ui_reports as ui_reports


class LorawanStep(conformance_testing.test_step_sequence.Step):
    """
    Base class of all the LoRaWAN tests.
    Expected reception: any LoRaWAN message.
    Sends after check: None.
    """
    def __init__(self, ctx_test_manager, step_name, default_rx1_window=True, next_step=None):
        """
        Adds a flag to indicate the preferred downlink window (RX1 or RX2) to use for sending messages to the DUT.
        :param ctx_test_manager: Test Manager of the Test Case.
        :param step_name: string representation of the step name.
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        :param next_step: next step of the test.
        """
        super().__init__(next_step=next_step, step_name=step_name, ctx_test_manager=ctx_test_manager)
        self.default_rx1_window = default_rx1_window

    def basic_check(self, received_testscript_msg_bytes):
        """
        Basic check for all the LoRaWAN test steps. It verifies the MIC of the message and sets a flag if the
        received message if of a CONFIRMED_UP type (so an ACK could be sent to the DUT).
        """
        super().basic_check(received_testscript_msg_bytes=received_testscript_msg_bytes)
        self.received_testscript_msg = flora_messages.GatewayMessage(
            json_ttm_str=received_testscript_msg_bytes.decode())
        lorawan_msg = self.received_testscript_msg.parse_lorawan_message()
        mtype_str = lorawan_msg.mhdr.mtype_str
        # Register in flag if the received message needs Acknowdlegment knowdlege
        if mtype_str in ('CONFIRMED_UP',):
            self.ctx_test_manager.device_under_test.message_to_ack = True
        else:
            self.ctx_test_manager.device_under_test.message_to_ack = False

        network_key = self.ctx_test_manager.device_under_test.loramac_params.nwkskey
        calculated_mic = lorawan_msg.calculate_mic(key=network_key)

        if not lorawan_msg.mic_bytes == calculated_mic:
            description_template = "Wrong MIC.\nKey: {key}\nMIC: {received_mic}\nCalculated: {calc}"
            raise lorawan_errors.MICError(description=description_template.format(
                                                key=utils.bytes_to_text(network_key),
                                                received_mic=utils.bytes_to_text(lorawan_msg.mic_bytes),
                                                calc=utils.bytes_to_text(calculated_mic)),
                                          test_case=self.ctx_test_manager.tc_name,
                                          step_name=self.name,
                                          last_message=self.received_testscript_msg.get_printable_str())

    def check_act_ok(self, received_frmpayload):
        """
        Checks if the received frame payload (FRMPayload) corresponds to a correctly
        formatted activation OK message (TAOK).

        (Step, bytes) -> (None)

        :param received_frmpayload: received byte sequence of the FRMPayload plain text.
        :return: None
        """
        downlink_counter = self.ctx_test_manager.ctx_test_session_coordinator.downlink_counter
        if not received_frmpayload == struct.pack('>H', downlink_counter):
            raise lorawan_errors.ActokCounterError(
                description="Received counter {} -> expected {}.".format(
                    received_frmpayload, struct.pack('>H', downlink_counter)),
                step_name=self.name,
                test_case=self.ctx_test_manager.tc_name,
                last_message=self.received_testscript_msg.get_printable_str()
            )

    def pingpong_echo_exchange(self, next_step=None):
        send_ping, check_pong = lorawan.lorawan_utils.generate_pingpong()
        if next_step:
            next_step.expected_bytes = check_pong
        else:
            self.next_step = check_pong

        end_device = self.ctx_test_manager.device_under_test
        lw_response = end_device.prepare_lorawan_data(frmpayload=send_ping,
                                                      fport=224)
        return lw_response, send_ping, check_pong

    def get_jointrigger(self):
        end_device = self.ctx_test_manager.device_under_test
        lw_response = end_device.prepare_lorawan_data(frmpayload=tests_parameters.TEST_CODE.TRIGGER_JOIN,
                                                      fport=224)
        return lw_response

    def raise_unexpected_response_error(self, last_message_bytes):
        self.received_testscript_msg = flora_messages.GatewayMessage(json_ttm_str=last_message_bytes.decode())
        exeption_raised = test_errors.UnexpectedResponseError(description="Unexpected msg.",
                                                              test_case=self.ctx_test_manager.tc_name,
                                                              step_name=self.name,
                                                              last_message=str(self.received_testscript_msg))
        ui_publisher.testingtool_log(msg_str=str(exeption_raised),
                                     key_prefix=message_broker.service_names.test_session_coordinator)
        raise exeption_raised

    def step_handler(self, ch, method, properties, body):
        """ Actions performed in this step of the test"""
        if not self.received_testscript_msg:
            self.received_testscript_msg = lorawan.parsing.flora_messages.GatewayMessage(json_ttm_str=body.decode())


class JoinRequestHandlerStep(LorawanStep):
    """
    Step that can handle join request messages, responding with a Join Accept message with the LoRaWAN MAC parameters
    configuration.
    Expected reception: Join Request message.
    Sends after check: Join Accept message.
    """

    def __init__(self,
                 ctx_test_manager,
                 step_name,
                 next_step,
                 default_rx1_window=True,
                 accept_dlsettings=lorawan.lorawan_parameters.general.DLSETTINGS.RX1OFFSET0_RX2DR0,
                 accept_rxdelay=lorawan.lorawan_parameters.general.JOIN_ACCEPT_RXDELAY.DELAY0,
                 accept_cflist=lorawan.lorawan_parameters.general.JOIN_ACCEPT_CFLIST.NO_CHANNELS):
        """
        This step has attributes with the desired parameter configuration to be sent in the Join Accept message.

        :param ctx_test_manager: Test Manager of the Test Case.
        :param step_name: string representation of the step name.
        :param next_step: next step of the test.
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        :param accept_dlsettings: byte sequence of the
        downlink settings to be configured using the Join Accept (RX1 offset and RX2 DR).
        :param accept_rxdelay: byte sequence of the configuration of the RX delay to be included in the Join Accept.
        :param accept_cflist: byte sequence of the channel list to be configured in the Join Accept.
        """
        super().__init__(ctx_test_manager=ctx_test_manager, step_name=step_name, next_step=next_step,
                         default_rx1_window=default_rx1_window)
        self.accept_dlsettings = accept_dlsettings
        self.accept_rxdelay = accept_rxdelay
        self.accept_cflist = accept_cflist

    def process_join_request(self, body_bytes):
        """
        Process a Join Request message and sends the Join Accept in the default RX1 with the configured parameters.
        :param body_bytes: byte sequence of the Join Request.
        :return: None.
        """
        if not self.received_testscript_msg:
            self.received_testscript_msg = flora_messages.GatewayMessage(json_ttm_str=body_bytes.decode())

        lw_joinrequest = self.received_testscript_msg.parse_lorawan_message()
        devnonce = lw_joinrequest.macpayload.devnonce_bytes
        end_device = self.ctx_test_manager.device_under_test
        previous_rx1_dr = end_device.loramac_params.rx1_dr_offset
        previous_rx2_dr = end_device.loramac_params.rx2_dr
        jaccept_phypayload = self.ctx_test_manager.device_under_test.accept_join(devnonce=devnonce,
                                                                                 dlsettings=self.accept_dlsettings,
                                                                                 rxdelay=self.accept_rxdelay,
                                                                                 cflist=self.accept_cflist)
        if self.default_rx1_window:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=jaccept_phypayload,
                delay=end_device.loramac_params.joinaccept_delay1,
                datr_offset=previous_rx1_dr)
        else:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=jaccept_phypayload,
                delay=end_device.loramac_params.joinaccept_delay2,
                data_rate=previous_rx2_dr,
                frequency=end_device.loramac_params.rx2_frequency)
        self.send_downlink(routing_key=message_broker.routing_keys.toAgent + '.gw1',
                           msg=json_nwk_response)

        self.print_step_info(
            received_str=self.received_testscript_msg.get_printable_str(),
            sending=jaccept_phypayload,
            additional_message="Session Updated.\n" + str(self.ctx_test_manager.device_under_test))

    def step_handler(self, ch, method, properties, body):
        """ Accepts a join request if it has the correct format and is not a replay (devnonce not previously used)."""
        if not self.received_testscript_msg:
            self.received_testscript_msg = flora_messages.GatewayMessage(json_ttm_str=body.decode())
        lw_joinrequest = self.received_testscript_msg.parse_lorawan_message()
        if lw_joinrequest.mhdr.mtype_str == "JOIN_REQUEST":
            self.process_join_request(body_bytes=body)
        else:
            raise test_errors.UnexpectedResponseError(description="A Join Request message was expected.",
                                                      step_name=self.name,
                                                      last_message=self.received_testscript_msg.get_printable_str(),
                                                      test_case=self.ctx_test_manager.tc_name)


class WaitDataToActivate(JoinRequestHandlerStep):
    """
    Waiting for any DATA message from the DUT and ready to respond with a
    test activation message. This step is a Join Request Handler, so it could be configured to handle a Join Request
    in case that the node ask for a session update (given that the DUT is not in Test Mode).
    Expected reception: Data message.
    Sends after check: Test Activation Message, FRMPayload plain text 0x01010101.
    """
    def step_handler(self, ch, method, properties, body):
        """
        Actions performed in this step of the test.
        """

        if not self.received_testscript_msg:
            self.received_testscript_msg = flora_messages.GatewayMessage(json_ttm_str=body.decode())
        frmpayload_response = tests_parameters.FRMPAYLOAD.TEST_ACT
        lw_received = self.received_testscript_msg.parse_lorawan_message()
        mtype_str = lw_received.mhdr.mtype_str
        if mtype_str == "JOIN_REQUEST":
            self.process_join_request(body_bytes=body)
        # If it's a TESTING MESSAGE (LoRaWAN data using port 224):
        elif (mtype_str in ('UNCONFIRMED_UP', 'CONFIRMED_UP') and
                not lw_received.macpayload.fport_int == 224):
            end_device = self.ctx_test_manager.device_under_test
            lw_response = end_device.prepare_lorawan_data(frmpayload=frmpayload_response,
                                                          fport=224)
            if self.default_rx1_window:
                json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                    phypayload=lw_response,
                    delay=end_device.loramac_params.rx1_delay,
                    datr_offset=end_device.loramac_params.rx1_dr_offset)
            else:
                json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                    phypayload=lw_response,
                    delay=end_device.loramac_params.rx2_delay,
                    data_rate=end_device.loramac_params.rx2_dr,
                    frequency=end_device.loramac_params.rx2_frequency)
            self.send_downlink(routing_key=message_broker.routing_keys.toAgent+'.gw1',
                               msg=json_nwk_response)
            self.ctx_test_manager.ctx_test_session_coordinator.downlink_counter = 0
            self.print_step_info(sending=frmpayload_response)
        else:
            raise test_errors.UnexpectedResponseError(description="Waiting for a data message (any port but 224).",
                                                      step_name=self.name,
                                                      last_message=self.received_testscript_msg.get_printable_str(),
                                                      test_case=self.ctx_test_manager.tc_name)


class WaitActokStep(LorawanStep):
    """
    Waits for an Activation Ok message to make a basic check of the downlink counter.
    Other more elaborated steps that add checks and send messages to the DUT could be inherited from this.
    Expected reception: TAOK message.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ Checks the downlink counter of an Activation Ok message."""
        if not self.received_testscript_msg:
            self.received_testscript_msg = flora_messages.GatewayMessage(json_ttm_str=body.decode())
        lw_message = self.received_testscript_msg.parse_lorawan_message()
        appskey = self.ctx_test_manager.device_under_test.loramac_params.appskey
        received_frmpayload = lw_message.get_frmpayload_plaintext(key=appskey)

        mtype_str = lw_message.mhdr.mtype_str
        if (mtype_str in ('UNCONFIRMED_UP', 'CONFIRMED_UP') and
                lw_message.macpayload.fport_int == 224 and
                len(received_frmpayload) == 2 and
                received_frmpayload[0:1] != lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG):
            self.check_act_ok(received_frmpayload=received_frmpayload)
        else:
            raise test_errors.UnexpectedResponseError(description="Waiting for an ACT OK with downlink counter.",
                                                      step_name=self.name,
                                                      last_message=self.received_testscript_msg.get_printable_str(),
                                                      test_case=self.ctx_test_manager.tc_name)


class ActokFinal(WaitActokStep):
    """
    Checks the TAOK message and if it's OK the test is finished with a PASS result.
    Expected reception: Activation Ok message (TAOK).
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ Process TAOK and finishes test with PASS result if its format is correct."""
        super().step_handler(ch, method, properties, body)
        self.print_step_info()
        self.success()


class WaitConfirmedActOk(WaitActokStep):
    """
    Checks the TAOK and verifies that it comes in a CONFIRMED_UP message.
    Expected reception: Activation Ok message (TAOK).
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ Checks the downlink counter of an Activation Ok message."""
        super().step_handler(ch, method, properties, body)
        lw_message = self.received_testscript_msg.parse_lorawan_message()
        mtype_str = lw_message.mhdr.mtype_str
        if mtype_str not in ('CONFIRMED_UP',):
            raise test_errors.InteroperabilityError(description="Waiting for a CONFIRMED_UP message.",
                                                    step_name=self.name,
                                                    last_message=self.received_testscript_msg.get_printable_str(),
                                                    test_case=self.ctx_test_manager.tc_name)


class ActokToPing(WaitActokStep):
    """
    Waiting for a new Activation OK message from the DUT.
    Expected reception: Activation Ok.
    Sends after check: Ping message.
    """
    def step_handler(self, ch, method, properties, body):
        """
        Pings with the previously configured reception windows lorawan_parameters
        after receiving an Activation Ok message (TAOK).
        Expected reception: Activation Ok.
        Sends after check: Ping message.
        """
        super().step_handler(ch, method, properties, body)

        lw_response, send_ping, _ = self.pingpong_echo_exchange(next_step=self.next_step)
        if self.default_rx1_window:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=lw_response,
                delay=self.ctx_test_manager.device_under_test.loramac_params.rx1_delay,
                datr_offset=self.ctx_test_manager.device_under_test.loramac_params.rx1_dr_offset)
        else:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=lw_response,
                delay=self.ctx_test_manager.device_under_test.loramac_params.rx2_delay,
                data_rate=self.ctx_test_manager.device_under_test.loramac_params.rx2_dr,
                frequency=self.ctx_test_manager.device_under_test.loramac_params.rx2_frequency)

        self.send_downlink(routing_key=message_broker.routing_keys.toAgent+'.gw1',
                           msg=json_nwk_response)
        self.print_step_info(sending=send_ping)


class ActokToTriggerJoin(WaitActokStep):
    """
    Expected reception: Activation Ok.
    Sends after check: Triggers Join Request.
    """
    def step_handler(self, ch, method, properties, body):
        """ Triggers a Join Request from the DUT after receiving an Activation Ok message."""
        super().step_handler(ch, method, properties, body)

        lw_response = self.get_jointrigger()
        if self.default_rx1_window:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=lw_response,
                delay=self.ctx_test_manager.device_under_test.loramac_params.rx1_delay,
                datr_offset=self.ctx_test_manager.device_under_test.loramac_params.rx1_dr_offset)
        else:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=lw_response,
                delay=self.ctx_test_manager.device_under_test.loramac_params.rx2_delay,
                data_rate=self.ctx_test_manager.device_under_test.loramac_params.rx2_dr,
                frequency=self.ctx_test_manager.device_under_test.loramac_params.rx2_frequency)
        self.send_downlink(routing_key=message_broker.routing_keys.toAgent+'.gw1',
                           msg=json_nwk_response)
        self.ctx_test_manager.device_under_test.set_default_loramac()
        self.print_step_info(sending=tests_parameters.TEST_CODE.TRIGGER_JOIN)


class CountingStep(WaitActokStep):
    """
    Waiting for Activation Ok messages and checking downlink counter.
    The tests remains in this steps for message_count number of messages (e.g. 2 activation messages)
    Expected reception: Activation Ok.
    Sends after check: None.
    """
    def __init__(self, ctx_test_manager, step_name, next_step, count_limit, default_rx1_window=True):
        """
        The test will be in this step so next step is a reference to itself.
        It keeps the message count.
        """
        super().__init__(ctx_test_manager=ctx_test_manager, step_name=step_name, next_step=self,
                         default_rx1_window=default_rx1_window)
        self.message_count = 0
        self._number_of_msg = count_limit

    def step_handler(self, ch, method, properties, body):
        """ Actions performed in this step of the test"""
        super().step_handler(ch, method, properties, body)
        self.message_count += 1
        self.print_step_info(additional_message="Received {0}/{1}.".format(self.message_count,
                                                                           self._number_of_msg))


class CountingFinalStep(CountingStep):
    """
    Counts TAOK messages and finalizes the test with a PASS result in case of receiving the configured amount
    of correct TAOK messages.
    Expected reception: Activation Ok.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ Actions performed in this step of the test"""
        super().step_handler(ch, method, properties, body)
        if self.message_count >= self._number_of_msg:
            self.message_count = 0
            self.success()


class FrequencyCheck(WaitActokStep):
    """
    Waiting for Activation Ok messages (TAOK) to check the downlink counter. Moreover, it verifies that all
    the configured frequencies are used by the DUT. After 5 times the number of configured frequencies all
    the values are expected to be used.
    Expected reception: Activation Ok.
    Sends after check: None.
    """
    def __init__(self, ctx_test_manager, step_name, next_step, default_rx1_window=True):
        """
        The test will be in this step so next step is a reference to itself.
        It keeps the message count.
        """
        super().__init__(step_name=step_name,
                         next_step=self,
                         default_rx1_window=default_rx1_window,
                         ctx_test_manager=ctx_test_manager)
        self.frequencies_to_check = None
        self.message_count = 0
        self._limit_of_msg = None
        self.step_after_checking = next_step

    def step_handler(self, ch, method, properties, body):
        """ Actions performed in this step of the test"""
        if not self.frequencies_to_check:
            self.frequencies_to_check = {
                key: 0
                for key in
                self.ctx_test_manager.device_under_test.loramac_params.channel_struct.used_frequencies}
            self._limit_of_msg = len(
                self.ctx_test_manager.device_under_test.loramac_params.channel_struct.used_frequencies) * 5
        super().step_handler(ch, method, properties, body)
        self.message_count += 1
        used_freq = self.received_testscript_msg.freq
        if used_freq not in self.ctx_test_manager.device_under_test.loramac_params.channel_struct.used_frequencies:
            self.frequencies_to_check[used_freq] = 1
        else:
            self.frequencies_to_check[used_freq] += 1
        str_template = "Received:{0}.\n({1})\n Count {2} of {3} limit."
        self.print_step_info(additional_message=str_template.format(used_freq,
                                                                    self.frequencies_to_check,
                                                                    self.message_count,
                                                                    self._limit_of_msg))
        if all(self.frequencies_to_check.values()):
            self.next_step = self.step_after_checking
        elif self.message_count >= self._limit_of_msg:
            raise lorawan_errors.FrequencyError(
                description="Not all the configured frequencies were used after {0} messages.\n({1})\n".format(
                    self.message_count,
                    self.frequencies_to_check),
                step_name=self.name,
                test_case=self.ctx_test_manager.tc_name,
                last_message=self.received_testscript_msg.get_printable_str()
            )


class FrequencyCheckFinal(FrequencyCheck):
    """
    Performs the frequency usage verification and ends the test with a PASS result if all frequencies are being used.
    Expected reception: Activation Ok.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)
        if all(self.frequencies_to_check.values()):
            self.next_step = self.step_after_checking
            self.success()


class ForbiddenFrequency(WaitActokStep):
    """
    Waiting for Activation Ok messages (TAOK) to check that after a pre-defined number of TAOK some frequencies
    are not being used. The number of messages to wait until considering that the DUT is not using any of the
    forbidden frequencies is 3 times the number of frequencies configured in the DUT LoRaWAN MAC parameters.
    Expected reception: Activation Ok.
    Sends after check: None.
    """
    def __init__(self, ctx_test_manager, forbiden_freq_list, step_name, next_step, default_rx1_window=True):
        """
        The test will be in this step so next step is a reference to itself.
        It keeps the message count.
        :param ctx_test_manager: Test Manager of the Test Case.
        :param forbiden_freq_list: list of frequencies that should not be used by the DUT.
        :param step_name: string representation of the step name.
        :param next_step: next step of the test.
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        """
        super().__init__(step_name=step_name, next_step=self, default_rx1_window=default_rx1_window,
                         ctx_test_manager=ctx_test_manager)
        self.forbidden_freq_list = forbiden_freq_list
        self.step_after_checking = next_step
        self._limit_of_msg = len(
            self.ctx_test_manager.device_under_test.loramac_params.channel_struct.used_frequencies) * 3
        self.message_count = 0

    def step_handler(self, ch, method, properties, body):
        """ Actions performed in this step of the test."""

        super().step_handler(ch, method, properties, body)
        self.message_count += 1
        used_freq = self.received_testscript_msg.freq
        if used_freq in self.forbidden_freq_list:
            raise lorawan_errors.FrequencyError(
                description="The frequency {0} was removed and shouldn't be used.\n(Forbidden: {1})\n".format(
                    used_freq,
                    self.forbidden_freq_list),
                step_name=self.name,
                test_case=self.ctx_test_manager.tc_name,
                last_message=self.received_testscript_msg.get_printable_str()
            )
        else:
            str_template = "Received:{0}.\nForbidden: ({1})\n Count {2} of {3} limit."
            self.print_step_info(additional_message=str_template.format(used_freq,
                                                                        self.forbidden_freq_list,
                                                                        self.message_count,
                                                                        self._limit_of_msg))
        if self.message_count >= self._limit_of_msg:
            self.next_step = self.step_after_checking


class WaitPong(LorawanStep):
    """
    The tests is waiting for the Pong response to the last Ping message sent.
    Expected reception: PONG message.
    Sends after check: None.
    """
    def __init__(self, ctx_test_manager, step_name, next_step, default_rx1_window=True):
        """
        The expected_bytes attribute MUST be set by a previous step before the handler is called.
        :param ctx_test_manager: Test Manager of the Test Case.
        :param step_name: string representation of the step name.
        :param next_step: next step of the test.
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        """
        super().__init__(ctx_test_manager=ctx_test_manager, step_name=step_name, next_step=next_step,
                         default_rx1_window=default_rx1_window)
        self.expected_bytes = None

    def step_handler(self, ch, method, properties, body):
        """ Pong message handler."""
        if not self.received_testscript_msg:
            self.received_testscript_msg = flora_messages.GatewayMessage(json_ttm_str=body.decode())

        received_lorawan = self.received_testscript_msg.parse_lorawan_message()

        appskey = self.ctx_test_manager.device_under_test.loramac_params.appskey
        received_frmpayload = received_lorawan.get_frmpayload_plaintext(key=appskey)

        mtype_str = received_lorawan.mhdr.mtype_str
        if mtype_str in ('UNCONFIRMED_UP', 'UNCONFIRMED_DOWN', 'CONFIRMED_UP', 'CONFIRMED_DOWN'):
            if (received_lorawan.macpayload.fport_int == 224 and
                    received_frmpayload[0:1] == lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG):

                if not received_frmpayload == self.expected_bytes:
                    raise lorawan_errors.EchoError(
                        description="PONG {0} received when expecting {1}.".format(
                            utils.bytes_to_text(received_frmpayload),
                            self.expected_bytes),
                        step_name=self.name,
                        test_case=self.ctx_test_manager.tc_name,
                        last_message=self.received_testscript_msg.get_printable_str(encryption_key=appskey))
            else:
                # If it's a data message, but not a PONG, the FRMPayload is decrypted and showed in the GUI.
                raise test_errors.UnexpectedResponseError(
                    description="Waiting for a PONG response.",
                    step_name=self.name,
                    last_message=self.received_testscript_msg.get_printable_str(encryption_key=appskey),
                    test_case=self.ctx_test_manager.tc_name)
        else:
            raise test_errors.UnexpectedResponseError(description="Waiting for a PONG response.",
                                                      step_name=self.name,
                                                      last_message=self.received_testscript_msg.get_printable_str(),
                                                      test_case=self.ctx_test_manager.tc_name)


class ProcessPong(WaitPong):
    """
    The tests is waiting for the Pong response to the last Ping message sent, and prints step completion information
    if the PONG message is correct.
    Expected reception: PONG message.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ PONG message handler, print step info if OK."""
        super().step_handler(ch, method, properties, body)
        self.print_step_info()


class PongFinalStep(WaitPong):
    """
    The tests is waiting for the Pong response to the last Ping message sent, and prints step completion information
    if the PONG message is correct. The test finishes with a PASS result if the PONG message is correct.
    Expected reception: PONG message.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ PONG message handler, test PASS if PONG is ok."""
        super().step_handler(ch, method, properties, body)
        self.print_step_info()
        self.success()


class PongToPing(WaitPong):
    """
    Sends a new ping message after receiving a correct pong.
    Expected reception: PONG message.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ Checks pong and sends a new ping using RX2."""
        super().step_handler(ch, method, properties, body)

        lw_response, send_ping, _ = self.pingpong_echo_exchange(next_step=self.next_step)

        device = self.ctx_test_manager.device_under_test
        if self.default_rx1_window:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=lw_response,
                delay=device.loramac_params.rx1_delay,
                datr_offset=device.loramac_params.rx1_dr_offset)
        else:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=lw_response,
                delay=device.loramac_params.rx2_delay,
                data_rate=device.loramac_params.rx2_dr,
                frequency=device.loramac_params.rx2_frequency)
        self.send_downlink(routing_key=message_broker.routing_keys.toAgent+'.gw1',
                           msg=json_nwk_response)
        self.print_step_info(sending=send_ping)


class PrintAnyMessage(LorawanStep):
    """
    Auxiliary class that receives any message, parses it and show it's content. Responds sending a downlink
    message with the Test Mode deactivation (FRMPayload plain text 0x00).
    Expected reception: Any message.
    Sends after check: Test Mode deactivation (FRMPayload plain text 0x00).
    """
    def step_handler(self, ch, method, properties, body):
        if not self.received_testscript_msg:
            self.received_testscript_msg = flora_messages.GatewayMessage(json_ttm_str=body.decode())

        frmpayload_response = tests_parameters.FRMPAYLOAD.TEST_DEACTIVATE
        end_device = self.ctx_test_manager.device_under_test
        lw_response = end_device.prepare_lorawan_data(frmpayload=frmpayload_response,
                                                      fport=224)
        if self.default_rx1_window:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=lw_response,
                delay=end_device.loramac_params.rx1_delay,
                datr_offset=end_device.loramac_params.rx1_dr_offset)
        else:
            json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
                phypayload=lw_response,
                delay=end_device.loramac_params.rx2_delay,
                data_rate=end_device.loramac_params.rx2_dr,
                frequency=end_device.loramac_params.rx2_frequency)
        self.send_downlink(routing_key=message_broker.routing_keys.toAgent+'.gw1',
                           msg=json_nwk_response)
        received_lorawan = self.received_testscript_msg.parse_lorawan_message(ignore_format_errors=True)

        step_report = ui_reports.InputFormBody(
            title="{TC}: Print message".format(TC=self.ctx_test_manager.tc_name.upper()),
            tag_key=self.ctx_test_manager.tc_name,
            tag_value=" ")

        step_report.add_field(ui_reports.ParagraphField(name="Received in Step: {}".format(self.name),
                                                        value=str(received_lorawan)))
        step_report.add_field(ui_reports.ParagraphField(name="Sent in Step: {}".format(self.name),
                                                        value=str(lorawan_parser.LoRaWANMessage(lw_response))))
        ui_publisher.display_on_gui(msg_str=str(step_report),
                                    key_prefix=message_broker.service_names.test_session_coordinator)
        self.print_step_info(sending=tests_parameters.FRMPAYLOAD.TEST_DEACTIVATE)


