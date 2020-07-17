"""
LoRaWAN Specification v1.0.2
Test Case Group: MAC_Commands
Test Name: MAC_01
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


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test MAC 01: Test the DevStatusReq MAC Command, both piggybacked in FOpts field and sent in the
    FRMPayload using port 0.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        self.s4_devstatusans_finalstep = mac_steps.DevStatusAnsCheckFinal(ctx_test_manager=self,
                                                                          step_name="S4DevStatusAnsFinal",
                                                                          next_step=None)
        self.add_step_description(step_name="Step 4: S4DevStatusAnsFinal",
                                  description=(
                                      "Verifies the reception of the DevStatusAns.\n"
                                      "- Reception from DUT: TAOK message with a DevStatusAns MAC Command.\n"
                                      "- TAS sends:  None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s3_actok_to_devstatusreq = mac_steps.ActokToDevStatusReq(ctx_test_manager=self,
                                                                      step_name="S3ActokToDevStatusReq_FRMPayload",
                                                                      next_step=self.s4_devstatusans_finalstep,
                                                                      piggybacked=False,
                                                                      in_frmpayload=True)
        self.add_step_description(step_name="Step 3: S3ActokToDevStatusReq_FRMPayload",
                                  description=(
                                      "After receiving a Act Ok message, a DevStatusReq is sent "
                                      "in FRMPayload using FPort=0.\n"
                                      "- Reception from DUT:After receiving a Act Ok message, a DevStatusReq is sent "
                                      "in FRMPayload using FPort=0.\n"
                                      "- TAS sends: DevStatusReq MAC command in FRMPayload using port 0.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s2_devstatusans_check = mac_steps.DevStatusAnsCheck(ctx_test_manager=self,
                                                                 step_name="S2DevStatusAns",
                                                                 next_step=self.s3_actok_to_devstatusreq)
        self.add_step_description(step_name="Step 2: S2DevStatusAns",
                                  description=(
                                      "Verifies the reception of the DevStatusAns.\n"
                                      "- Reception from DUT: TAOK message with a DevStatusAns MAC Command.\n"
                                      "- TAS sends:  None.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s1_actok_to_devstatusreq = mac_steps.ActokToDevStatusReq(ctx_test_manager=self,
                                                                      step_name="S1ActokToDevStatusReq_Piggybacked",
                                                                      next_step=self.s2_devstatusans_check,
                                                                      piggybacked=True,
                                                                      in_frmpayload=False)
        self.add_step_description(step_name="Step 1: S1ActokToDevStatusReq_Piggybacked",
                                  description=(
                                      "After receiving a Act Ok message, a DevStatusReq is sent piggybacked "
                                      "using the FOpts field.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends:  DevStatusReq MAC command piggybacked in FOpts field.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_devstatusreq
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_",
                                  description=(
                                      "Objective: Test the DevStatusReq MAC Command, both piggybacked in FOpts "
                                      "field and sent in the FRMPayload using port 0.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode.\n"))


