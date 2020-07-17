"""
LoRaWAN Specification v1.0.2
Test Case Group: Functionality
Test Name: FUN_02
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
import conformance_testing.test_errors as test_errors


class ActokToPingDelay(lorawan_steps.ActokToPing):
    """
    Checks the tolerance to delays in timing from the specified start of the reception windows.
    Expected reception: Activation Ok.
    Sends after check: Ping message with an extra delay.
    """

    def __init__(self, ctx_test_manager, step_name, delay, next_step, default_rx1_window=True):
        """

        :param ctx_test_manager: Test Manager of the Test Case.
        :param step_name: string representation of the step name.
        :param delay: extra delay in microseconds (positive or negative).
        :param next_step: next step of the test.
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        """
        super().__init__(ctx_test_manager=ctx_test_manager, step_name=step_name, default_rx1_window=default_rx1_window,
                         next_step=next_step)
        self.delay = delay

    def step_handler(self, ch, method, properties, body):
        self.ctx_test_manager.device_under_test.loramac_params.rx1_delay += self.delay
        try:
            super().step_handler(ch, method, properties, body)
        except test_errors.TestingToolError as tt_e:
            raise tt_e
        finally:
            self.ctx_test_manager.device_under_test.loramac_params.rx1_delay -= self.delay


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test FUN 02: Test the node's tolerance to timing errors in the download reception windows.

    PRECONDITION: DUT (Device Under Test) is already in TEST MODE.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        self.s8_check_pong = lorawan_steps.PongFinalStep(ctx_test_manager=self, step_name="S8WaitPong",
                                                         next_step=None)
        self.add_step_description(step_name="Step 8: 8WaitPong",
                                  description=(
                                      "Checks the reception of the PONG message.\n"
                                      "- Reception from DUT: PONG message.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s7_actok_to_ping_m20rx2 = ActokToPingDelay(ctx_test_manager=self, step_name="S7ActokToPingDelayMinus20",
                                                        delay=-20,
                                                        next_step=self.s8_check_pong,
                                                        default_rx1_window=False)
        self.add_step_description(step_name="Step 7: S7ActokToPingDelayMinus20",
                                  description=(
                                      "Waits and Activation Ok message with the current downlink counter of "
                                      "the session and after it's received a PING PONG exchange will be initiated, "
                                      "using RX2 with a timing error of -20 micro seconds.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: PING message with a -20 micro seconds delay in RX2.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s6_check_pong = lorawan_steps.ProcessPong(ctx_test_manager=self, step_name="S6WaitPong",
                                                       next_step=self.s7_actok_to_ping_m20rx2)
        self.add_step_description(step_name="Step 6: 6WaitPong",
                                  description=(
                                      "Checks the reception of the PONG message.\n"
                                      "- Reception from DUT: PONG message.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s5_actok_to_ping_m20rx1 = ActokToPingDelay(ctx_test_manager=self,
                                                        step_name="S5ActokToPingDelay",
                                                        delay=-20,
                                                        next_step=self.s6_check_pong,
                                                        default_rx1_window=True)
        self.add_step_description(step_name="Step 5: S5ActokToPingDelayMinus20",
                                  description=(
                                      "Waits and Activation Ok message with the current downlink counter of "
                                      "the session and after it's received a PING PONG exchange will be initiated, "
                                      "using RX1 with a timing error of -20 micro seconds.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: PING message with a -20 micro seconds delay in RX1.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s4_check_pong = lorawan_steps.ProcessPong(ctx_test_manager=self, step_name="S4WaitPong",
                                                       next_step=self.s5_actok_to_ping_m20rx1)
        self.add_step_description(step_name="Step 4: S4WaitPong",
                                  description=(
                                      "Checks the reception of the PONG message.\n"
                                      "- Reception from DUT: PONG message.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s3_actok_to_ping_20rx2 = ActokToPingDelay(ctx_test_manager=self, step_name="S3ActokToPingDelayPlus20",
                                                       delay=20,
                                                       next_step=self.s4_check_pong,
                                                       default_rx1_window=False)
        self.add_step_description(step_name="Step 2: S3ActokToPingDelayPlus20",
                                  description=(
                                      "Waits and Activation Ok message with the current downlink counter of "
                                      "the session and after it's received a PING PONG exchange will be initiated, "
                                      "using RX2 with a timing error of +20 micro seconds.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: PING message with a +20 micro seconds delay in RX2.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s2_check_pong = lorawan_steps.ProcessPong(ctx_test_manager=self, step_name="S2WaitPong",
                                                       next_step=self.s3_actok_to_ping_20rx2)
        self.add_step_description(step_name="Step 2: S2WaitPong",
                                  description=(
                                      "Checks the reception of the PONG message.\n"
                                      "- Reception from DUT: PONG message.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s1_actok_to_ping_20rx1 = ActokToPingDelay(ctx_test_manager=self, step_name="S1ActokToPingDelayPlus20",
                                                       delay=20,
                                                       next_step=self.s2_check_pong,
                                                       default_rx1_window=True)
        self.add_step_description(step_name="Step 1: S1ActokToPingDelayPlus20",
                                  description=(
                                      "Waits and Activation Ok message with the current downlink counter of "
                                      "the session and after it's received a PING PONG exchange will be "
                                      "initiated, using RX1 with a timing error of +20 micro seconds.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: PING message with a +20 micro seconds delay in RX1.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_ping_20rx1
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_FUN_02",
                                  description=(
                                      "Objective: Test the node's tolerance to timing errors in the download "
                                      "reception windows. Verifies that downlink messages with +/- 20us in RX1 "
                                      "and RX2 are correctly received.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode and supports "
                                      "Over The Air Activation (OTAA).\n"))



