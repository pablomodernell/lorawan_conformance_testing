"""
LoRaWAN Specification v1.0.2
Test Case Group: MAC_Commands
Test Name: MAC_02
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

    LoRaWAN Test MAC 02: Test that the DUT ignores a frame if MAC commands are present both in payload and in
    FOpts field.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)

        # ------------------------------------------------------------------------------------------------
        self.s4_no_maccommand_finalstep = mac_steps.NoMACCommandCheckFinal(ctx_test_manager=self,
                                                                           step_name="S4NoMACCommandCheck",
                                                                           next_step=None)
        self.add_step_description(step_name="Step 4: S4NoMACCommandCheck.",
                                  description=(
                                      "Verifies that the TAOK message doesn't have a DevStatusAns "
                                      "and sends other DevStatusReq in FRMPayload and in FOpts field. "
                                      "This message must be ignored.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: Two DevStatusReq mac commands, one in FRMPayload "
                                      "and other piggybacked.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s3_actok_to_devstatusreq = mac_steps.ActokToDevStatusReq(ctx_test_manager=self,
                                                                      step_name="S3ActokToDevStatusReq_double",
                                                                      next_step=self.s4_no_maccommand_finalstep,
                                                                      piggybacked=True,
                                                                      in_frmpayload=True)
        self.add_step_description(step_name="Step 3: S3ActokToDevStatusReq_double",
                                  description=(
                                      "After receiving a TAOK, two DevStatusReq are sent in the FRMPayload "
                                      "and in FOpts field. This message must be ignored.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: Two DevStatusReq mac commands, one in FRMPayload "
                                      "and other piggybacked.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s2_no_maccommand_check = mac_steps.NoMACCommandCheck(ctx_test_manager=self,
                                                                  step_name="S2NoMACCommandCheck",
                                                                  next_step=self.s3_actok_to_devstatusreq)
        self.add_step_description(step_name="Step 2: S2NoMACCommandCheck.",
                                  description=(
                                      "Verifies that the TAOK message doesn't have a DevStatusAns "
                                      "and sends another DevStatusReq in FRMPayload and in FOpts field. "
                                      "This message must be ignored.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: Two DevStatusReq mac commands, one in FRMPayload "
                                      "and other piggybacked.\n"))

        # ------------------------------------------------------------------------------------------------
        self.s1_actok_to_devstatusreq = mac_steps.ActokToDevStatusReq(ctx_test_manager=self,
                                                                      step_name="S1ActokToDevStatusReq_double",
                                                                      next_step=self.s2_no_maccommand_check,
                                                                      piggybacked=True,
                                                                      in_frmpayload=True)
        self.add_step_description(step_name="Step 1: S1ActokToDevStatusReq_double",
                                  description=(
                                      "After receiving a TAOK, two DevStatusReq are sent in the FRMPayload "
                                      "and in FOpts field. This message must be ignored.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: Two DevStatusReq mac commands, one in FRMPayload "
                                      "and other piggybacked.\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_devstatusreq
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_MAC_02",
                                  description=(
                                      "Objective: Test that the DUT ignores a frame if MAC commands are present both "
                                      "in payload and in FOpts field.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode.\n"))

