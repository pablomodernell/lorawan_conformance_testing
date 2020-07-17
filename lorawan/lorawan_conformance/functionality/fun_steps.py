"""
LoRaWAN Specification v1.0.2
Test Case Group: Functionalities (FUN)
This modules includes all the test Steps that are common to the FUN group.
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
import lorawan.lorawan_conformance.lorawan_errors as lorawan_errors
import lorawan.lorawan_conformance.lorawan_steps as lorawan_steps
import lorawan.lorawan_parameters.testing as tests_parameters
import lorawan.lorawan_parameters.general as lorawan_parameters
import parameters.message_broker as message_broker


class CountCheckFCntUp(lorawan_steps.CountingStep):
    """
    The Test Case remains in this step (is a CountingStep) until the reception of a specified
    number of messages (TAOK) and checks the Frame Counter UP of the received messages. After verifying the
    retransmission the UNCONFIRMED frames are configured again for the subsequent uplink transmissions.
    This is a final step, its completion means the that the Test Case result is PASS.
    Expected reception: TAOK.
    Sends after check: None.
    """

    def __init__(self,
                 ctx_test_manager,
                 step_name,
                 count_limit,
                 next_step,
                 default_rx1_window=True,
                 sequence_increment=1):
        """

        :param ctx_test_manager:
        :param step_name:
        :param count_limit:
        :param next_step:
        :param default_rx1_window:
        :param sequence_increment:
        """
        super().__init__(ctx_test_manager=ctx_test_manager,
                         step_name=step_name,
                         count_limit=count_limit,
                         default_rx1_window=default_rx1_window,
                         next_step=next_step)
        self.last_fcntup = None
        self.sequence_increment = sequence_increment

    def step_handler(self, ch, method, properties, body):
        """ Actions performed in this step of the test"""
        super().step_handler(ch, method, properties, body)
        lorawan_received = self.received_testscript_msg.parse_lorawan_message()

        received_fcntup_int = lorawan_received.macpayload.fhdr.get_fcnt_int()
        if not self.last_fcntup:
            self.last_fcntup = received_fcntup_int
        else:
            if (self.last_fcntup + self.sequence_increment) == received_fcntup_int:
                self.last_fcntup = received_fcntup_int
            else:
                appskey = self.ctx_test_manager.device_under_test.loramac_params.appskey
                raise lorawan_errors.FCntError(
                    description="Previous Uplink FCnt: {p} -> Received: {r} (expecting: {e})".format(
                        p=self.last_fcntup,
                        r=received_fcntup_int,
                        e=self.last_fcntup+self.sequence_increment),
                    test_case=self.ctx_test_manager.tc_name,
                    step_name=self.name,
                    last_message=self.received_testscript_msg.get_printable_str(encryption_key=appskey)
                )
        if self.message_count >= self._number_of_msg:
            frmpayload_response = tests_parameters.TEST_CODE.USE_UNCONFIRMED
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
            self.send_downlink(routing_key=message_broker.routing_keys.toAgent + '.gw1',
                               msg=json_nwk_response)
            self.message_count = 0
            self.success()


class ActOkToSetConfirmed(lorawan_steps.WaitActokStep):
    """
    Checks the TAOK and triggers the usage of confirmed uplink frames.
    Expected reception: TAOK.
    Sends after check: Activates the CONFIRMED_UP for all the subsequent uplink frames (Test ID 2).
    """
    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)

        frmpayload_response = tests_parameters.TEST_CODE.USE_CONFIRMED

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
        self.print_step_info(sending=frmpayload_response)


class CheckConfirmedToACK(lorawan_steps.WaitConfirmedActOk):
    """
    Checks the TAOK verifying that the message if of the type CONFIRMED_UP, and triggers the usage of UNCONFIRMED
    uplink messages for the subsequent transmissions.
    Expected reception: TAOK.
    Sends after check: Activates the UNCONFIRMED type for all the subsequent uplink frames (Test ID 2).
    """
    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)

        end_device = self.ctx_test_manager.device_under_test
        lw_response = end_device.prepare_lorawan_data(frmpayload=tests_parameters.TEST_CODE.USE_UNCONFIRMED,
                                                      fport=224,
                                                      fctr=lorawan_parameters.FCTRL.DOWN_ADROFF_ACKON_FPENDOFF_FOPTLEN0)
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
        self.print_step_info()


class CheckConfirmedToACKFinal(CheckConfirmedToACK):
    """ The tests finishes with result PASS if the TAOK is correct and comes in a CONFIRMED message. Final step."""
    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)
        self.success()
