"""
LoRaWAN Specification v1.0.2
Test Case Group: Activation
Test Name: ACT_01
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

    LoRaWAN Test ACT 01: Test Mode activation to test the device's Activation By Personalization (ABP).
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)

        # ------------------------------------------------------------------------------------------------
        # Step 2, waiting test accept: the test is waiting for test accepted app message in port 224.
        self.s2_actok_finalstep = lorawan_steps.ActokFinal(ctx_test_manager=self,
                                                           step_name="S2ActokFinalStep",
                                                           next_step=None)
        self.add_step_description(step_name="Step 2: S2ActokFinalStep",
                                  description=("The test is expecting a Test Activation Ok message with the current "
                                               "downlink counter\n"
                                               "- Reception from DUT: TAOK message with the downlink counter.\n"
                                               "- TAS sends: none"))

        # ------------------------------------------------------------------------------------------------
        # Step 1, waiting any: the test is waiting for any data packet to arrive in a port different from 0
        self.s1_data_to_activate = lorawan_steps.WaitDataToActivate(ctx_test_manager=self,
                                                                    step_name="S1DataToActivate",
                                                                    next_step=self.s2_actok_finalstep)
        self.add_step_description(step_name="Step 1: S1DataToActivate",
                                  description=("Wait any data from the DUT to activate Test Mode.\n"
                                               "- Reception from DUT: DATA packet.\n"
                                               "- TAS sends: Test Mode activation message to the DUT "
                                               "(DL packet with payload 0x01010101 sent to port 224). "
                                               "The payload is encrypted with the AppSKey.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_data_to_activate
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_ACT_01",
                                  description=(
                                      "Objective: Check that the node can join using ABP and enter "
                                      "Test Mode Activation.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions:\n"
                                      "The end device has a pre-configured DevAddr, NwkSKey and AppSKey.\n"
                                      "The Test Application Server has the end device registered in its device list\n"
                                      "and knows its NwkSkey, AppSKey and DevAddr.\n"))
