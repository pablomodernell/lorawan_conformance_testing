"""
LoRaWAN Specification v1.0.2
Test Case Group: Functionality
Test Name: FUN_05
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
    The TestAppManager (Test Application Manager) is a TestManager defined in each test,
    it specifies the different steps that the test performs.

    LoRaWAN Test FUN 05: Test the implementation of confirmed packets, verifies the handling
    of the ACK bit in the uplink messages.

    PRECONDITION: DUT (Device Under Test) is in TEST MODE.
    """

    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # -----------------------------------------------------------------------------------------
        self.s2_check_confirmed_final = fun_steps.CheckConfirmedToACKFinal(
            ctx_test_manager=self,
            step_name="S2CheckConfirmedAndACK",
            next_step=None,
            default_rx1_window=True)
        self.add_step_description(
            step_name="Step 2: S2CheckConfirmedAndACK",
            description=(
                "Configures again the usage of UNCONFIRMED frames and sends the ACK.\n"
                "- Reception from DUT: TAOK message with the downlink counter.\n"
                "- TAS sends:  ACK the messages and configures the UNCONFIRMED uplink frames "
                "(plain text FRMPaylod=0x03).\n"))
        # -----------------------------------------------------------------------------------------
        self.s1_actok_to_setconfirmed = fun_steps.ActOkToSetConfirmed(
            ctx_test_manager=self,
            step_name="S1ActOKToSetConfirmed",
            next_step=self.s2_check_confirmed_final,
            default_rx1_window=True)
        self.add_step_description(
            step_name="Step 1: S1ActOKToSetConfirmed",
            description=(
                "Checks the downlink counter of the TAOK message and configures the node "
                "to use CONFIRMED uplink frames sending a test ID 2.\n"
                "- Reception from DUT: TAOK message with the downlink counter.\n"
                "- TAS sends:  Triggers the usage of CONFIRMED uplink frames "
                "(plain text FRMPaylod=0x02).\n"))

        # -----------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_setconfirmed
        self.add_step_description(
            step_name="Test ID: TD_LoRaWAN_FUN_05",
            description=(
                "Objective: Test the implementation of confirmed packets, verifies the handling "
                "of the ACK bit in the uplink messages.\n"
                "References: LoRaWAN Specification v1.0.2.\n"
                "The DUT has an active session with the TAS and is in Test Mode.\n"))
