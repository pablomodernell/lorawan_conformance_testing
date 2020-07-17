"""
LoRaWAN Specification v1.0.2
Test Case Group: MAC_Commands
Test Name: SEC_02
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
import lorawan.lorawan_conformance.lorawan_steps as lorawan_steps
import conformance_testing.test_step_sequence
import parameters.message_broker as message_broker
from utils import bytes_to_text


class ActokToWrongMIC(lorawan_steps.WaitActokStep):
    """
    Test started and waiting for an Activation OK message from the DUT to check if a message with wrong MIC is
    ignored by the device under test.
    Expected reception: Activation Ok.
    Sends after check: Ping message with a wrong MIC.
    """
    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)
        lw_response, send_ping, _ = self.pingpong_echo_exchange(next_step=self.next_step)
        lw_response_wrong_mic = lw_response[:-4:] + b'\xff\xff\xff\xff'
        device = self.ctx_test_manager.device_under_test
        json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
            phypayload=lw_response_wrong_mic,
            delay=device.loramac_params.rx1_delay,
            datr_offset=device.loramac_params.rx1_dr_offset)
        self.send_downlink(
            msg=json_nwk_response,
            routing_key=message_broker.routing_keys.toAgent+'.gw1')
        # Manually decrease the downlink counter.
        self.ctx_test_manager.ctx_test_session_coordinator.downlink_counter -= 1
        self.print_step_info(sending=send_ping,
                             additional_message="Modified MIC: {} ->{}\n".format(bytes_to_text(lw_response[-4::]),
                                                                                 bytes_to_text(b'\xff\xff\xff\xff')))


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test SEC 02: Test if a message with a wrong MIC is ignored as expected.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        # Step 2, verifies Act Ok: verifies that the last ping message with wrong MIC
        #  was ignored (downlink counter unchanged).
        self.s2_actok_final = lorawan_steps.ActokFinal(ctx_test_manager=self,
                                                       step_name="S2WaitOkFinal",
                                                       next_step=None)
        self.add_step_description(step_name="Step 2: S2WaitOkFinal",
                                  description=(
                                      "Check that the last PING was ignored.\n"
                                      "- Reception from DUT: TAOK message.\n"
                                      "- TAS sends:  None.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 1, send wrong mic:
        # the test is waiting for an Act OK message to send a ping with a wrong MIC (to be ignored)
        self.s1_actok_to_ping = ActokToWrongMIC(ctx_test_manager=self, step_name="S1ActokToWrongMIC",
                                                next_step=self.s2_actok_final)
        self.add_step_description(step_name="Step 1: S1ActokToWrongMIC",
                                  description=(
                                      "Wait an ACT OK from the DUT to send a PING with wrong MIC.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: PING message with wrong MIC.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_ping
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_",
                                  description=(
                                      "Objective: Test if a message with a wrong MIC is ignored as expected.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode.\n"))

