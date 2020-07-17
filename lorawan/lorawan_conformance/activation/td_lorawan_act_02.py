"""
LoRaWAN Specification v1.0.2
Test Case Group: Activation
Test Name: ACT_02
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
import conformance_testing.test_step_sequence
import lorawan.lorawan_conformance.lorawan_steps as lorawan_steps


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test ACT 02: Over the air activation (OTAA) modifying RX1 and RX2 parameters.

    PRECONDITION: DUT (Device Under Test) is already in TEST MODE, and the node supports OTAA.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        # Step 6, waiting pong.
        self.s6_pong_finalstep = lorawan_steps.PongFinalStep(ctx_test_manager=self, step_name="S6PongFinalStep",
                                                             next_step=None)
        self.add_step_description(step_name="Step 6: S6PongFinalStep",
                                  description=(
                                      "Checks the last PONG.\n"
                                      "- Reception from DUT: PONG message.\n"
                                      "- TAS sends:  none.\n"))
        # ------------------------------------------------------------------------------------------------
        # Step 5, waiting pong: Checks PONG and sends a new PING.
        self.s5_pong_to_ping = lorawan_steps.PongToPing(ctx_test_manager=self, step_name="S5PongToPing",
                                                        next_step=self.s6_pong_finalstep,
                                                        default_rx1_window=False)
        self.add_step_description(step_name="Step 5: S5PongToPing",
                                  description=(
                                      "Waits for the PONG message and sends another PING, now using RX2.\n"
                                      "- Reception from DUT: PONG message.\n"
                                      "- TAS sends:  PING message using RX2.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 4, waiting new activation: Check the activation and send pong using specified new DR in RX1.
        self.s4_actok_to_ping = lorawan_steps.ActokToPing(ctx_test_manager=self, step_name="S4ActokToPing",
                                                          next_step=self.s5_pong_to_ping)
        self.add_step_description(step_name="Step 4: S4ActokToPing",
                                  description=(
                                      "After receiving an TAOK (Activation OK) message with the current downlink "
                                      "counter, a PING message will be sent.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends:  PING message in RX1 using a DR offset of 2.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 3, session updated: waiting for a data message to activate again the test mode.
        self.s3_data_to_activate = lorawan_steps.WaitDataToActivate(
            ctx_test_manager=self,
            step_name="S3DataToActivate",
            next_step=self.s4_actok_to_ping,
            accept_dlsettings=general_parameters.DLSETTINGS.RX1OFFSET2_RX2DR3)
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
            lorawan_steps.JoinRequestHandlerStep(ctx_test_manager=self,
                                                 step_name="S2JoinRequestToAccept", next_step=self.s3_data_to_activate,
                                                 accept_dlsettings=general_parameters.DLSETTINGS.RX1OFFSET2_RX2DR3))
        self.add_step_description(step_name="Step 2: S2JoinRequestToAccept",
                                  description=(
                                      "Updates the session information of the device.\n"
                                      "- Reception from DUT: Join Request message.\n"
                                      "- TAS sends: Join Accept message configuring DLSettings "
                                      "(RX1DRoffset=2 and RX2DR=3).\n"))
        # ------------------------------------------------------------------------------------------------
        # Step 1, waiting actok: the test is waiting for an Activation OK message with the downlink counter.
        self.s1_actok_to_triggerjoin = lorawan_steps.ActokToTriggerJoin(ctx_test_manager=self,
                                                                        step_name="S1ActokToTriggerJoin",
                                                                        next_step=self.s2_joinrequest_to_accept)
        self.add_step_description(step_name="Step 1: S1ActokToTriggerJoin",
                                  description=(
                                      "Waits a TAOK (Activation Ok) message with the current downlink counter of"
                                      "the session and, after it's received, a new session request will be triggered.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: Trigger join request with Test ID 6.\n"))
        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_triggerjoin
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_ACT_02",
                                  description=(
                                      "Objective: Test Over the Air Activation, changing DR of RX windows. "
                                      "Check that the node can join using OTAA in RX1 and RX2.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode and supports "
                                      "Over The Air Activation (OTAA).\n"))

