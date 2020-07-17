"""
LoRaWAN Specification v1.0.2
Test Case Group: MAC_Commands
Test Name: MAC_04
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
import lorawan.lorawan_parameters.general as general_parameters


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test MAC 04: Checks the channel addition implementation verifying that the new added frequencies are used.
    Adds multiple channels in a single message.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)

        # ------------------------------------------------------------------------------------------------
        self.s4_config_accepted = mac_steps.NewChannelAnsCheckFinal(ctx_test_manager=self,
                                                                    step_name="S4NewChannelAnsAcceptCheck",
                                                                    next_step=None,
                                                                    number_of_requests=3,
                                                                    is_accept_expected=True)
        self.add_step_description(step_name="Step 4: S4NewChannelAnsAcceptCheck",
                                  description=(
                                      "Verifies that the DUT sends a NewChannelAns MAC Command accepting "
                                      "the removed frequencies.\n"
                                      "- Reception from DUT: message with NewChannelAns answer from the DUT "
                                      "accepting the removed channels (Status OK).\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s3_actok_to_removechannels = mac_steps.ActokToNewChannelReq(
            ctx_test_manager=self,
            step_name="S3ActokToNewChannelReq_RemoveChannels",
            next_step=self.s4_config_accepted,
            freq_idx_tuple_list=[
                (0, 3),
                (0, 4),
                (0, 5)],
            piggybacked=False,
            in_frmpayload=True)
        self.add_step_description(step_name="Step 3: S3ActokToNewChannelReq_RemoveChannels",
                                  description=(
                                      "Removes the previously added channels.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: NewChannelReq removing the previously added channels.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s2_config_accepted = mac_steps.NewChannelAnsCheck(ctx_test_manager=self,
                                                               step_name="S2NewChannelAnsAcceptCheck",
                                                               next_step=self.s3_actok_to_removechannels,
                                                               number_of_requests=3,
                                                               is_accept_expected=True)
        self.add_step_description(step_name="Step 2: S2NewChannelAnsAcceptCheck.",
                                  description=(
                                      "Verifies that the DUT sends a NewChannelAns MAC Command accepting "
                                      "the new added frequencies.\n"
                                      "- Reception from DUT: message with NewChannelAns answer from the DUT "
                                      "accepting the added channels (Status OK).\n"
                                      "- TAS sends: None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s1_actok_to_addchannels = mac_steps.ActokToNewChannelReq(
            ctx_test_manager=self,
            step_name="S1ActokToNewChannelReq_AddChannels",
            next_step=self.s2_config_accepted,
            freq_idx_tuple_list=[
                (general_parameters.VALID_FREQ[22], 3),
                (general_parameters.VALID_FREQ[23], 4),
                (general_parameters.VALID_FREQ[24], 5)],
            piggybacked=False,
            in_frmpayload=True)
        self.add_step_description(step_name="Step 1: S1ActokToNewChannelReq_AddChannels.",
                                  description=(
                                      "Adds new frequencies using NewChannelReq MAC Commands.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: message with multiple NewChannelReq MAC Commands.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_addchannels
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_MAC_04",
                                  description=(
                                      "Objective: Checks the channel addition implementation verifying that the "
                                      "new added frequencies are used. Adds multiple channels in a single message.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode.\n"))
