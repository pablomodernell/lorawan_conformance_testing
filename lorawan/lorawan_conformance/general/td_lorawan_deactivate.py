"""
LoRaWAN Specification v1.0.2
Test Case Group: General (Auxiliary test)
Test Name: DEACTIVATE
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


class ActOkToDeactivate(lorawan_steps.WaitActokStep):
    """
    Waiting for an actok message to arrive to deactivate the
    test mode on the End Device.
    Expected reception: TAOK.
    Sends after check: Test Mode deactivation message (plain text FRMPayload=0x00).
    """
    def step_handler(self, ch, method, properties, body):
        """ Test pass if the Activation Ok message is received without an error."""
        super().step_handler(ch, method, properties, body)

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
        self.ctx_test_manager.ctx_test_session_coordinator.downlink_counter = 0
        self.success()


class TestAppManager(conformance_testing.test_step_sequence.TestManager):
    """
    The TestAppManager (Test Application Manager) is a TestManager defined in each test, it specifies the
    different steps that the test performs.

    LoRaWAN Test DEACTIVATION: Deactivates test mode.
    """
    def __init__(self, test_session_coordinator):
        super().__init__(
            test_name=__name__.split(".")[-1],
            ctx_test_session_coordinator=test_session_coordinator)
        # ------------------------------------------------------------------------------------------------
        # Step 1, waiting TAOK: the test is waiting for a TAOK message with the downlink counter to deactivate the
        # Test Mode.
        self.s1_actok_to_deactivate = ActOkToDeactivate(ctx_test_manager=self,
                                                        step_name="S1ActOkToDeactivate", next_step=None)
        self.add_step_description(step_name="Step 1: S1ActOkToDeactivate",
                                  description=(
                                      "Verifies TAOK and deactivates Test Mode.\n"
                                      "- Reception from DUT: TAOK message with the downlink counter.\n"
                                      "- TAS sends: Test Mode deactivation (payload 0x00).\n"))

        # ------------------------------------------------------------------------------------------------
        # Set Initial Step
        self.current_step = self.s1_actok_to_deactivate
        self.add_step_description(step_name="Test ID: TD_LoRaWAN_DEACTIVATE",
                                  description=(
                                      "Objective: Deactivates test mode.\n"
                                      "References: LoRaWAN Specification v1.0.2.\n"
                                      "Pre-test conditions: The DUT is in Test Mode.\n"))

