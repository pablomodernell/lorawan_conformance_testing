"""
LoRaWAN Specification v1.0.2
Test Case Group: MAC_Commands
Test Name: SEC_01
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


class RepeatedPingPong(lorawan_steps.PongToPing):
    def __init__(self, ctx_test_manager, step_name, next_step, count_limit, default_rx1_window=True):
        """
        Repeated PING PONG exchanges are initiated by the TAS to check the implementation of the cryptography mechanism.
        Expected reception: PONG message (response of a previously sent PING).
        Sends after check: PING message.
        """
        super().__init__(ctx_test_manager=ctx_test_manager, step_name=step_name, next_step=self,
                         default_rx1_window=default_rx1_window)
        self.message_count = 0
        self.number_of_msg = count_limit
        self.jump_after_complete = next_step

    def step_handler(self, ch, method, properties, body):
        """ Actions performed in this step of the test"""
        self.message_count += 1
        if self.message_count >= self.number_of_msg:
            self.message_count = 0
            self.next_step = self.jump_after_complete
        super().step_handler(ch, method, properties, body)


class ProcessPongFinal(lorawan_steps.ProcessPong):
    """
    Checks the PONG message and if it's correct the test case ends with a PASS result.
    Expected reception: PONG message (response of a previously sent PING).
    Sends after check: None.
    """

    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)
        self.success()


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test SEC 01: Test the encryption of the LoRaWAN data messages by the exchange of PING PONG echo messages.
    """

    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)

        # ------------------------------------------------------------------------------------------------
        # Step 3, waiting pong: verifies the last pong response.
        self.s3_pong_finalstep = ProcessPongFinal(ctx_test_manager=self,
                                                  step_name="S3PongFinal", next_step=None)
        self.add_step_description(step_name="Step 3: S3PongFinal.",
                                  description=(
                                      "Verifies the last PONG message, if it is correct the test case result is PASS.\n"
                                      "- Reception from DUT: PONG message (response of a previously sent PING).\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 2, waiting test accept: the test is waiting for test accepted app message in port 224.
        self.s2_repeat_pongtoping = RepeatedPingPong(ctx_test_manager=self,
                                                     step_name="S2RepeatedPingPong",
                                                     next_step=self.s3_pong_finalstep,
                                                     count_limit=10,
                                                     default_rx1_window=True)
        self.add_step_description(step_name="Step : _",
                                  description=(
                                      "Initiates 10 PING PONG exchanges to check the cryptography implementation.\n"
                                      "- Reception from DUT: PONG message (response of a previously sent PING).\n"
                                      "- TAS sends: PING message.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 1, waiting any: the test is waiting for any data packet to arrive in a port different from 0
        self.s1_actok_to_ping = lorawan_steps.ActokToPing(ctx_test_manager=self,
                                                          step_name="S1ActokToPing",
                                                          next_step=self.s2_repeat_pongtoping)
        self.add_step_description(step_name="Step 1: S1ActokToPing",
                                  description=(
                                      "Wait an ACT OK from the DUT to initate a PING PONG exchange.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: PING message.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_ping
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_SEC_01",
                                  description=(
                                      "Objective: Test the encryption of the LoRaWAN data messages by the exchange "
                                      "of PING PONG echo messages.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode.\n"))


