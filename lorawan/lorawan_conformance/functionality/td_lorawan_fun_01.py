"""
LoRaWAN Specification v1.0.2
Test Case Group: Functionality
Test Name: FUN_01
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


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test FUN 01: Basic test application functionality. Initiates a PING PONG echo exchange and verifies
    the TAOK downlink counter.

    PRECONDITION: DUT (Device Under Test) is already in TEST MODE.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        # Step 3, counting: waiting for activation ok message to check downlink.
        self.s3_count_finalstep = lorawan_steps.CountingFinalStep(ctx_test_manager=self, step_name="S3CountFinalStep",
                                                                  next_step=None,
                                                                  count_limit=2)
        self.add_step_description(step_name="Step 3: S3CountFinalStep.",
                                  description=(
                                      "Count a predefined amount (2) of TAOK messages.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends:  None.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 2, waiting pong response: the test is waiting for test accepted app message in port 224.
        self.s2_pong_to_count = lorawan_steps.ProcessPong(ctx_test_manager=self, step_name="S2ProcessPong",
                                                          next_step=self.s3_count_finalstep)
        self.add_step_description(step_name="Step 2: S2ProcessPong",
                                  description=(
                                      "After the PONG message is received, a count is started.\n"
                                      "- Reception from DUT: PONG message.\n"
                                      "- TAS sends:  None.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 1, waiting actok: the test is waiting for an Activation OK message with the downlink counter
        self.s1_actok_to_ping = lorawan_steps.ActokToPing(ctx_test_manager=self, step_name="S1ActokToPing",
                                                          next_step=self.s2_pong_to_count,
                                                          default_rx1_window=True)
        self.add_step_description(step_name="Step 1: S1ActokToPing",
                                  description=(
                                      "Waits for a TAOK (Activation Ok) message with the current downlink counter of "
                                      "the session and after it's received a PING PONG exchange will be initiated.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: PING message.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_ping
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_FUN_01",
                                  description=(
                                      "Objective: Basic test application functionality with a message exchange. "
                                      "Initiates a PING PONG echo exchange and verifies the TAOK downlink counter.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT has an active session with the TAS and "
                                      "is in Test Mode.\n"))


