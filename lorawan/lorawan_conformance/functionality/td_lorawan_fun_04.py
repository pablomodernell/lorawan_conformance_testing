"""
LoRaWAN Specification v1.0.2
Test Case Group: Functionality
Test Name: FUN_04
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
import lorawan.lorawan_parameters.testing as tests_parameters


class ActokToWrongFCnt(lorawan_steps.WaitActokStep):
    """
    Test started and waiting for an TAOK (Activation OK) message from the DUT.
    Expected reception: Activation Ok.
    Sends after check: Unconfirmed frame using previous frame sequence number -1.
    """
    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)
        frmpayload_response = tests_parameters.FRMPAYLOAD.TEST_DEACTIVATE
        # Given that in self.fcnt_down is the next frame counter, (self.fcnt_down - 2) will be forced into the
        # LoRaWAN message in order to use the previous downlink sequence number minus 1.
        lw_response_wrong_fcnt = self.ctx_test_manager.device_under_test.prepare_lorawan_data(
            frmpayload=frmpayload_response,
            fport=224,
            force_fcntdown_int=self.ctx_test_manager.device_under_test.fcnt_down - 2)
        device = self.ctx_test_manager.device_under_test
        json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
            phypayload=lw_response_wrong_fcnt,
            delay=device.loramac_params.rx1_delay,
            datr_offset=device.loramac_params.rx1_dr_offset)
        self.send_downlink(
            msg=json_nwk_response,
            routing_key=message_broker.routing_keys.toAgent+'.gw1')
        # Manually decrease the downlink counter.
        self.ctx_test_manager.ctx_test_session_coordinator.downlink_counter -= 1
        self.print_step_info(sending=frmpayload_response,
                             additional_message="This message should be ignored.\nModified FCnt dl: {} ->{}\n".format(
                                 self.ctx_test_manager.device_under_test.fcnt_down,
                                 self.ctx_test_manager.device_under_test.fcnt_down - 2))


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test FUN 04: Checks that a message with decreasing downlink frame conuter is ignored.

    PRECONDITION: DUT (Device Under Test) is already in TEST MODE.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        self.s2_actok_final = lorawan_steps.ActokFinal(ctx_test_manager=self, step_name="S2ActokFinal", next_step=None)
        self.add_step_description(step_name="Step 2: S2ActokFinal",
                                  description=(
                                      "Waits and Activation Ok message with the current downlink counter.\n"
                                      "- Reception from DUT:\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s1_actok_to_wrongfcnt = ActokToWrongFCnt(ctx_test_manager=self, step_name="S1ActokToWrongFCnt",
                                                      next_step=self.s2_actok_final,
                                                      default_rx1_window=True)
        self.add_step_description(step_name="Step 1: S1ActokToWrongFCnt.",
                                  description=(
                                      "Waits and Activation Ok message with the current downlink counter of "
                                      "the session and after it's received a message with a decreasing frame downlink "
                                      "counter will be sent. This messages must be ignored.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends:  message with wrong frame downlink counter.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_wrongfcnt
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_FUN_04",
                                  description=(
                                      "Objective: Checks that a message with decreasing downlink frame counter "
                                      "is ignored.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT has an active session with the TAS and "
                                      "is in Test Mode.\n"))

        self.add_step_description(step_name="Step 2: s2_actok_final",
                                  description="Waits and Activation Ok message with the current downlink counter.")

