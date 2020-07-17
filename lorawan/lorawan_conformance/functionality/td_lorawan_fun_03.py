"""
LoRaWAN Specification v1.0.2
Test Case Group: Functionality
Test Name: FUN_03
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
import conformance_testing.test_step_sequence
import lorawan.lorawan_conformance.functionality.fun_steps as fun_steps


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test FUN 03: Check the handling of the uplink sequence number.

    PRECONDITION: DUT (Device Under Test) is already in TEST MODE.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        self.s1_count_fcntup = fun_steps.CountCheckFCntUp(ctx_test_manager=self,
                                                          step_name="S1CountCheckFCntUp",
                                                          count_limit=3,
                                                          next_step=None,
                                                          default_rx1_window=True)
        self.add_step_description(step_name="Step 1: S1CountCheckFCntUp",
                                  description=(
                                      "Count TAOK messages with the current downlink counter of "
                                      "the session and check that the uplink frame counter is incremented.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_count_fcntup
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_FUN_03",
                                  description=(
                                      "Objective: Check the handling of the uplink sequence number.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode.\n"))

