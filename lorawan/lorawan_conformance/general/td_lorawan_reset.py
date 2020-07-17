"""
LoRaWAN Specification v1.0.2
Test Case Group: General
Test Name: RESET
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
import lorawan.lorawan_parameters.testing as tests_parameters
import conformance_testing.test_step_sequence
import parameters.message_broker


class AnyToDeactivate(lorawan_steps.LorawanStep):
    """
    Step 1, waiting actok message: the test is waiting for an actok message to arrive to deactivate the
    test mode on the End Device.
    """
    def step_handler(self, ch, method, properties, body):
        """ Test pass if the Activation Ok message is received without an error."""
        frmpayload_response = tests_parameters.FRMPAYLOAD.TEST_DEACTIVATE
        end_device = self.ctx_test_manager.device_under_test
        lw_response = end_device.prepare_lorawan_data(frmpayload=frmpayload_response,
                                                      fport=224)
        json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
            phypayload=lw_response,
            delay=end_device.loramac_params.rx1_delay,
            datr_offset=end_device.loramac_params.rx1_dr_offset)
        self.send_downlink(routing_key=parameters.message_broker.routing_keys.toAgent+'.gw1',
                           msg=json_nwk_response)
        self.print_step_info(sending=tests_parameters.FRMPAYLOAD.TEST_DEACTIVATE)


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN DUT RESET: Auxiliary test, deactivates test mode to take the DUT to a known state to continue executing
    the remaining test cases in case of a test FAIL.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(test_name=__name__.split(".")[-1],
                         ctx_test_session_coordinator=test_session_coordinator)

        # ------------------------------------------------------------------------------------------------
        # Step 3, waiting test accept: the test is waiting for test accepted app message in port 224.
        self.s3_actok_finalstep = lorawan_steps.ActokFinal(ctx_test_manager=self,
                                                           step_name="S3ActokFinalStep", next_step=None)
        self.add_step_description(step_name="Step 3: S3ActokFinalStep",
                                  description=("The test is expecting a Test Activation Ok message with the current\n"
                                               "downlink counter\n"
                                               "- Reception from DUT: TAOK message with the downlink counter."
                                               "- TAS sends: none"))

        # ------------------------------------------------------------------------------------------------
        # Step 2, waiting any: the test is waiting for any data packet to arrive in a port different from 0
        self.s2_data_to_activate = lorawan_steps.WaitDataToActivate(ctx_test_manager=self,
                                                                    step_name="S2DataToActivate",
                                                                    next_step=self.s3_actok_finalstep)
        self.add_step_description(step_name="Step 2: S2DataToActivate",
                                  description=("Wait any data from the DUT to activate Test Mode.\n"
                                               "- Reception from DUT: DATA packet.\n"
                                               "- TAS sends: Test Mode activation message to the DUT"
                                               "(DL packet with payload 0x01010101 sent to port 224)\n"
                                               "The payload is encrypted with the AppSKey.\n"))

        # ------------------------------------------------------------------------------------------------
        # Step 1, waiting any message: deactivates the test mode.
        self.s1_any_to_deactivate = AnyToDeactivate(ctx_test_manager=self,
                                                    step_name="S1AnyToDeactivate", next_step=self.s2_data_to_activate)
        self.add_step_description(step_name="Step 1: S1AnyToDeactivate",
                                  description=(
                                      "Sends the Test Mode deactivation message after any received message.\n"
                                      "- Reception from DUT: Any LoRaWAN message.\n"
                                      "- TAS sends:  Test Mode deactivation (payload 0x00).\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_any_to_deactivate
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_RESET",
                                  description=(
                                      "Objective: Resets the DUT to a known state after a test fails, deactivating and "
                                      "activating again the Test Mode.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions:\n"
                                      "The end device has a pre-configured DevAddr, NwkSKey and AppSKey.\n"
                                      "The Test Application Server has the end device registered in its ABP "
                                      "device list and knows its NwkSkey, AppSKey and DevAddr.\n"))

