"""
LoRaWAN Specification v1.0.2
Test Case Group: Activation
Test Name: ACT_04
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
import lorawan.lorawan_parameters.general as general_parameters
import lorawan.lorawan_conformance.lorawan_steps as lorawan_steps
import conformance_testing.test_step_sequence


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test ACT 04: Over the air activation (OTAA), adding a new channel in the Join Accept message configuration.

    PRECONDITION: DUT (Device Under Test) is already in TEST MODE, and the node supports OTAA.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        # Step 4, waiting new activation: Check the activation and send pong using specified new DR in RX1.
        self.s4_verify_frequencies_final = lorawan_steps.FrequencyCheckFinal(ctx_test_manager=self,
                                                                             step_name="S4VerifyFrequencies",
                                                                             next_step=None,
                                                                             default_rx1_window=True)
        self.add_step_description(step_name="Step 4: S4VerifyFrequencies",
                                  description=(
                                      "The test stays in this step and verifies that all the frequencies "
                                      "are being used.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: none.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 3, session updated: waiting for a data message to activate again the test mode.
        self.s3_data_to_activate = lorawan_steps.WaitDataToActivate(ctx_test_manager=self, step_name="S3DataToActivate",
                                                                    next_step=self.s4_verify_frequencies_final,
                                                                    default_rx1_window=False,
                                                                    accept_cflist=general_parameters.get_cflist(
                                                                        general_parameters.VALID_FREQ[20],
                                                                        general_parameters.VALID_FREQ[21],
                                                                        general_parameters.VALID_FREQ[22],
                                                                        general_parameters.VALID_FREQ[23],
                                                                        general_parameters.VALID_FREQ[24]))
        self.add_step_description(step_name="Step 3: S3DataToActivate",
                                  description=(
                                      "A data message is expected, and the Test Mode will be activated "
                                      "after its reception.\n"
                                      "- Reception from DUT: DATA packet.\n"
                                      "- TAS sends: Test Mode activation message to the DUT"
                                      "(DL packet with payload 0x01010101 sent to port 224).\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 2, join triggered: the test is waiting for the join request from the DUT.
        self.s2_joinrequest_to_accept = (
            lorawan_steps.JoinRequestHandlerStep(ctx_test_manager=self, step_name="S2JoinrequestToAccept=12",
                                                 next_step=self.s3_data_to_activate,
                                                 accept_cflist=general_parameters.get_cflist(
                                                     general_parameters.VALID_FREQ[20],
                                                     general_parameters.VALID_FREQ[21],
                                                     general_parameters.VALID_FREQ[22],
                                                     general_parameters.VALID_FREQ[23],
                                                     general_parameters.VALID_FREQ[24]))
        )
        self.add_step_description(step_name="Step 2: S2JoinRequestToAccept",
                                  description=(
                                      "Waits for a join request message. A Join Accept "
                                      "will be sent in response configuring new channels (using CFList).\n"
                                      "- Reception from DUT: Join Request message.\n"
                                      "- TAS sends: Join Accept message configuring CFList to add new channels.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 1, waiting actok: the test is waiting for an Activation OK message with the downlink counter.
        self.s1_actok_to_triggerjoin = lorawan_steps.ActokToTriggerJoin(ctx_test_manager=self,
                                                                        step_name="S1ActokToTriggerJoin",
                                                                        next_step=self.s2_joinrequest_to_accept)
        self.add_step_description(step_name="Step 1: S1ActokToTriggerJoin",
                                  description=(
                                      "Waits and Activation Ok message with the current downlink counter of"
                                      "the session and, after it's received, a new session will be requested\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: Trigger join request with test ID 6.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_triggerjoin
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_ACT_04",
                                  description=(
                                      "Objective: Test Over the Air Activation configuring 5 new channels.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode and supports "
                                      "Over The Air Activation (OTAA).\n"))
