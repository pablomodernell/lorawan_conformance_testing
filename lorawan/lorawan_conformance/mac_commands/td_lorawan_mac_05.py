"""
LoRaWAN Specification v1.0.2
Test Case Group: MAC_Commands
Test Name: MAC_05
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
import lorawan.lorawan_parameters.general as general_parameters


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test MAC 05: Checks the channel addition implementation verifying that the new added frequencies are used.
    Addition of a single channel.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        self.s7_actok_finalstep = lorawan_steps.ActokFinal(ctx_test_manager=self,
                                                           step_name="S7ActokFinalStep",
                                                           next_step=None)
        self.add_step_description(step_name="Step 7: S7ActokFinalStep",
                                  description=(
                                      "Final step, check the last TAOK message.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s6_forbidden_frequency = lorawan_steps.ForbiddenFrequency(
            ctx_test_manager=self,
            step_name="S6ForbiddenFrequencyCheck",
            next_step=self.s7_actok_finalstep,
            default_rx1_window=True,
            forbiden_freq_list=[
                general_parameters.VALID_FREQ[22]])
        self.add_step_description(step_name="Step 6: S6ForbiddenFrequencyCheck",
                                  description=(
                                      "Verifies that the removed frequency is not used after the reception of "
                                      "a given number of downlink messages.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s5_config_accepted = mac_steps.NewChannelAnsCheck(ctx_test_manager=self,
                                                               step_name="S5NewChannelAnsAcceptCheck",
                                                               next_step=self.s6_forbidden_frequency,
                                                               number_of_requests=1,
                                                               is_accept_expected=True)
        self.add_step_description(step_name="Step 5: S5NewChannelAnsAcceptCheck",
                                  description=(
                                      "Verifies that the DUT accepted the channel removal.\n"
                                      "- Reception from DUT: NewChannelAns MAC Command with Status OK.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s4_actok_to_removech = mac_steps.ActokToNewChannelReq(ctx_test_manager=self,
                                                                   step_name="S4ActokToNewChannelReq_RemoveChannel",
                                                                   next_step=self.s5_config_accepted,
                                                                   freq_idx_tuple_list=[
                                                                       (0, 3)],
                                                                   piggybacked=False,
                                                                   in_frmpayload=True)
        self.add_step_description(step_name="Step 4: S4ActokToNewChannelReq_RemoveChannel",
                                  description=(
                                      "Removes the previously added channel. "
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: NewChannelReq removing the previously added channels.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s3_verify_frequencies = lorawan_steps.FrequencyCheck(ctx_test_manager=self,
                                                                  step_name="S3VerifyFrequencies",
                                                                  next_step=self.s4_actok_to_removech,
                                                                  default_rx1_window=True)
        self.add_step_description(step_name="Step 3: S3VerifyFrequencies.",
                                  description=(
                                      "Count TAOK messages to check that the new frequency is used.\n"
                                      "- Reception from DUT: TAOK messages until all the configured frequencies "
                                      "(including the newly added) are used.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s2_config_accepted = mac_steps.NewChannelAnsCheck(ctx_test_manager=self,
                                                               step_name="S2NewChannelAnsAcceptCheck",
                                                               next_step=self.s3_verify_frequencies,
                                                               number_of_requests=1,
                                                               is_accept_expected=True)
        self.add_step_description(step_name="Step 2: S2NewChannelAnsAcceptCheck.",
                                  description=(
                                      "Verifies that the DUT accepted the new added channel.\n"
                                      "- Reception from DUT: NewChannelAns MAC Command with Status OK.\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s1_actok_to_addchannels = mac_steps.ActokToNewChannelReq(ctx_test_manager=self,
                                                                      step_name="S1ActokToNewChannelReq_AddChannel",
                                                                      next_step=self.s2_config_accepted,
                                                                      freq_idx_tuple_list=[
                                                                          (general_parameters.VALID_FREQ[22], 3)],
                                                                      piggybacked=False,
                                                                      in_frmpayload=True)
        self.add_step_description(step_name="Step 1: S1ActokToNewChannelReq_AddChannel.",
                                  description=(
                                      "Adds a single new channel in the channel index 3.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: NewChannelReq MAC Command adding a new channel.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_addchannels

        self.add_step_description(step_name="Test ID: TD_LoRaWAN_MAC_05",
                                  description=(
                                      "Objective: Checks the channel addition implementation verifying that the "
                                      "new added frequencies are used. Addition of a single channel.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode and supports "
                                      "Over The Air Activation (OTAA).\n"))

