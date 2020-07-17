"""
LoRaWAN Specification v1.0.2
Test Case Group: MAC_Commands
Test Name: MAC_03
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
from lorawan.lorawan_conformance.mac_commands import mac_steps
import lorawan.lorawan_conformance.lorawan_steps as lorawan_steps


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test MAC 03: Check the channel addition implementation verifying that the new added frequencies are used.
    Try to remove a read-only default channel.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        self.s3_actok_to_check_frequency = lorawan_steps.FrequencyCheckFinal(ctx_test_manager=self,
                                                                             step_name="S3VerifyFrequencies",
                                                                             next_step=None,
                                                                             default_rx1_window=True)
        self.add_step_description(step_name="Step 2: S3VerifyFrequencies",
                                  description=(
                                      "The previous step had verified that the NewChannelAns contained a "
                                      "Not OK status. Now, this step checks a set of messages and all the "
                                      "configured frequencies must be used.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends:  None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s2_config_rejected = mac_steps.NewChannelAnsCheck(ctx_test_manager=self,
                                                               step_name="S2NewChannelRejectedCheck",
                                                               next_step=self.s3_actok_to_check_frequency,
                                                               number_of_requests=3,
                                                               is_accept_expected=False)
        self.add_step_description(step_name="Step 2: S2NewChannelRejectedCheck",
                                  description=(
                                      "Verifies that the default channel deletion was rejected by the DUT.\n"
                                      "- Reception from DUT: message with the NewChannelAns with status Not OK.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s1_actok_to_trydisableCh = mac_steps.ActokToNewChannelReq(
            ctx_test_manager=self,
            step_name="S1ActokToNewChannelReq_DisableDefault",
            next_step=self.s2_config_rejected,
            freq_idx_tuple_list=[(0, 0), (0, 1), (0, 2)],
            piggybacked=False,
            in_frmpayload=True)
        self.add_step_description(step_name="Step 1: S1ActokToNewChannelReq_DisableDefault.",
                                  description=(
                                      "Checks the TAOK message and tries to disable a default channel of the current "
                                      "LoRaWAN region.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends:  NewChannelReq MAC Command disabling a default channel.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_trydisableCh
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_MAC_03",
                                  description=(
                                      "Objective: Check the channel addition implementation, try to remove a "
                                      "read-only default channel.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode and supports "
                                      "Over The Air Activation (OTAA).\n"))

