"""
LoRaWAN Specification v1.0.2
Test Case Group: Functionalities (MAC)
This modules includes all the test Steps that are common to the MAC group.
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
import utils
import struct
import lorawan.lorawan_conformance.lorawan_steps as lorawan_steps
import parameters.message_broker as message_broker
import lorawan.lorawan_parameters.general as lorawan_parameters
import lorawan.parsing.mac_commands as mac_commands
import lorawan.lorawan_conformance.lorawan_errors as lorawan_errors


class NoMACCommandCheck(lorawan_steps.LorawanStep):
    """
    Verifies the TAOK message and checks that the received message doesn't contain MAC commands.
    Expected reception: TAOK.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ Test pass if the Activation Ok message is received without an error."""
        super().step_handler(ch, method, properties, body)
        lw_message = self.received_testscript_msg.parse_lorawan_message()
        appskey = self.ctx_test_manager.device_under_test.loramac_params.appskey
        received_frmpayload = lw_message.get_frmpayload_plaintext(key=appskey)

        mtype_str = lw_message.mhdr.mtype_str
        received_commands = []
        if (mtype_str in ('UNCONFIRMED_UP', 'CONFIRMED_UP') and
                lw_message.macpayload.fport_int == 0):
            received_commands.extend(mac_commands.CommandCreator.parse_mac_commands(
                direction_up=True,
                commands_byte_sequence=received_frmpayload
            ))
        received_commands.extend(lw_message.piggybacked_commands)
        if received_commands:
            commands_str = ""
            for command in received_commands:
                commands_str += str(command)
            raise lorawan_errors.MACError(
                description="No MAC command expected, but received:\n{comm}".format(comm=commands_str),
                test_case=self.ctx_test_manager.tc_name,
                step_name=self.name)
        else:
            if self.received_testscript_msg.parse_lorawan_message().macpayload.fport_int == 0:
                key = self.ctx_test_manager.device_under_test.loramac_params.nwkskey
            else:
                key = self.ctx_test_manager.device_under_test.loramac_params.appskey
            self.print_step_info(received_str=self.received_testscript_msg.get_printable_str(
                encryption_key=key))


class NoMACCommandCheckFinal(NoMACCommandCheck):
    """
    Verifies the TAOK message and checks that the received message doesn't contain MAC commands.
    This is a final steps, if this is verified ok the test result is PASS.
    Expected reception: TAOK.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ Test pass if the Activation Ok message is received without an error."""
        super().step_handler(ch, method, properties, body)
        self.success()


class ActokToMACCommand(lorawan_steps.WaitActokStep):
    """
    Check the TAOK message and sends a MAC command in the default reception window (RX1 or RX2). The MAC command
    could be configured to be sent on the FRMPayload (using port 0) or piggybacked (using FOpts field of the FHDR).
    Expected reception: TAOK.
    Sends after check: MAC command.
    """
    def __init__(self,
                 ctx_test_manager,
                 step_name,
                 next_step,
                 command_bytes,
                 default_rx1_window=True,
                 piggybacked=True,
                 in_frmpayload=False):
        """

        :param ctx_test_manager: Test Manager of the Test Case.
        :param step_name: string representation of the step name.
        :param next_step: next step of the test.
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        :param command_bytes: byte sequence of the MAC commands to be sent in the downlink message.
        :param piggybacked: flag to indicate if the commands should be copied in the FOpts filed of the message.
        :param in_frmpayload: flag to indicate if port 0 should be used and the commands copied in the FRMPayload.
        """
        super().__init__(ctx_test_manager=ctx_test_manager, step_name=step_name, next_step=next_step,
                         default_rx1_window=default_rx1_window)
        self.piggybacked = piggybacked
        self.in_frmpayload = in_frmpayload
        self.command_bytes = command_bytes

    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)
        frmpayload = None
        fport = None
        fctr = lorawan_parameters.FCTRL.DOWN_ADROFF_ACKOFF_FPENDOFF_FOPTLEN0
        fopts = b''
        if self.piggybacked:
            fctr = struct.pack('B', len(self.command_bytes) % 16)
            fopts = self.command_bytes
        if self.in_frmpayload:
            frmpayload = self.command_bytes
            fport = 0
        lw_response = self.ctx_test_manager.device_under_test.prepare_lorawan_data(
            frmpayload=frmpayload,
            fport=fport,
            mhdr=lorawan_parameters.MHDR.CONFIRMED_DOWN,
            fctr=fctr,
            fopts=fopts)
        device = self.ctx_test_manager.device_under_test
        json_nwk_response = self.received_testscript_msg.create_nwk_response_str(
            phypayload=lw_response,
            delay=device.loramac_params.rx1_delay,
            datr_offset=device.loramac_params.rx1_dr_offset)
        self.send_downlink(
            msg=json_nwk_response,
            routing_key=message_broker.routing_keys.toAgent+'.gw1')
        # manually decrease the downlink counter, because this message should be ignored by the DUT.
        if self.piggybacked and self.in_frmpayload:
            self.ctx_test_manager.ctx_test_session_coordinator.downlink_counter -= 1
        if self.received_testscript_msg.parse_lorawan_message().macpayload.fport_int == 0:
            key = self.ctx_test_manager.device_under_test.loramac_params.nwkskey
        else:
            key = self.ctx_test_manager.device_under_test.loramac_params.appskey
        self.print_step_info(
            received_str=self.received_testscript_msg.get_printable_str(
                encryption_key=key),
            additional_message="Sending MAC Command: 0x{comm}\nPiggybacked: {p}\nIn FRMPayload: {f}".format(
                comm=utils.bytes_to_text(self.command_bytes),
                p=self.piggybacked,
                f=self.in_frmpayload))


class MACCommandAnsCheck(lorawan_steps.LorawanStep):
    """
    Base class for the steps that verify that the DUT send an answer to a MAC command request from the TAS
    Expected reception: any LoRaWAN message.
    Sends after check: None.
    """
    def __init__(self,
                 ctx_test_manager,
                 step_name,
                 next_step,
                 default_rx1_window=True):
        """
        Defines a received commands list (empty by default) to be filled by the parsed MAC commands contained in
        this message.
        :param ctx_test_manager: Test Manager of the Test Case.
        :param step_name: string representation of the step name.
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        :param next_step: next step of the test.
        """
        super().__init__(ctx_test_manager=ctx_test_manager, step_name=step_name, next_step=next_step,
                         default_rx1_window=default_rx1_window)
        self.received_commands = []

    def step_handler(self, ch, method, properties, body):
        """ Test pass if the Activation Ok message is received without an error."""
        super().step_handler(ch, method, properties, body)
        lw_message = self.received_testscript_msg.parse_lorawan_message()
        appskey = self.ctx_test_manager.device_under_test.loramac_params.appskey
        received_frmpayload = lw_message.get_frmpayload_plaintext(key=appskey)

        mtype_str = lw_message.mhdr.mtype_str
        if (mtype_str in ('UNCONFIRMED_UP', 'CONFIRMED_UP') and
                lw_message.macpayload.fport_int == 0):
            self.received_commands.extend(mac_commands.CommandCreator.parse_mac_commands(
                direction_up=True,
                commands_byte_sequence=received_frmpayload
            ))
        self.received_commands.extend(lw_message.piggybacked_commands)


class NewChannelAnsCheck(MACCommandAnsCheck):
    """
    Verifies that the DUT sent an answer to a NewChannelReq MAC command request sent previouly by the TAS.
    Expected reception: any LoRaWAN message.
    Sends after check: None.
    """
    def __init__(self,
                 ctx_test_manager,
                 step_name,
                 next_step,
                 number_of_requests,
                 is_accept_expected=True,
                 default_rx1_window=True):
        """
        :param ctx_test_manager: Test Manager of the Test Case.
        :param step_name: string representation of the step name.
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        :param next_step: next step of the test.
        :param number_of_requests: Number of the newly configured channels.
        :param is_accept_expected: flag to indicate if the channels added are expected to be accepted or rejected.
        """
        super().__init__(ctx_test_manager=ctx_test_manager, step_name=step_name, next_step=next_step,
                         default_rx1_window=default_rx1_window)
        self.number_of_requests = number_of_requests
        self.accept_expected = is_accept_expected

    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)
        if self.received_testscript_msg.parse_lorawan_message().macpayload.fport_int == 0:
            key = self.ctx_test_manager.device_under_test.loramac_params.nwkskey
        else:
            key = self.ctx_test_manager.device_under_test.loramac_params.appskey
        if len(self.received_commands) >= self.number_of_requests:
            ans_checked = 0
            for command in self.received_commands:
                if type(command).__name__ == "NewChannelAns" and command.is_ok == self.accept_expected:
                    ans_checked += 1
            if ans_checked >= self.number_of_requests:
                self.print_step_info(received_str=self.received_testscript_msg.get_printable_str(
                    encryption_key=key))
            else:
                if self.accept_expected:
                    description_str = "Received {rec} NewChannelAns, expecting {exp}.\n".format(
                        rec=ans_checked,
                        exp=self.number_of_requests)
                else:
                    description_str = "The channel configuration asking to remove a default channel must be rejected.\n"
                    description_str += "Received {rec} rejection NewChannelAns, expecting {exp}.\n".format(
                        rec=ans_checked,
                        exp=self.number_of_requests)
                raise lorawan_errors.MACConfigurationExchangeError(
                    description=description_str,
                    test_case=self.ctx_test_manager.tc_name,
                    step_name=self.name,
                    last_message=self.received_testscript_msg.get_printable_str(
                                        encryption_key=key))
        else:
            raise lorawan_errors.NoMACResponseError(
                description="Expecting {} NewChannelAns.".format(self.number_of_requests),
                test_case=self.ctx_test_manager.tc_name,
                step_name=self.name,
                last_message=self.received_testscript_msg.get_printable_str(
                            encryption_key=key))


class NewChannelAnsCheckFinal(NewChannelAnsCheck):
    """
    Verifies that the DUT sent an answer to a NewChannelReq MAC command request sent previouly by the TAS.
    Final step, the test result is PASS if this step verification succeeds.
    Expected reception: any LoRaWAN message.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)
        self.success()


class ActokToDevStatusReq(ActokToMACCommand):
    """
    Checks the downlink conunter of the TAOK and sends a DevStatusReq MAC Command.
    Expected reception: TAOK message.
    Sends after check: DevStatusReq MAC Command.
    """
    def __init__(self,
                 ctx_test_manager,
                 step_name,
                 next_step,
                 default_rx1_window=True,
                 piggybacked=True,
                 in_frmpayload=False):
        commands = lorawan_parameters.MAC_COMMANDS.DevStatusReq
        super().__init__(ctx_test_manager=ctx_test_manager,
                         step_name=step_name,
                         next_step=next_step,
                         command_bytes=commands,
                         default_rx1_window=default_rx1_window,
                         piggybacked=piggybacked,
                         in_frmpayload=in_frmpayload)


class DevStatusAnsCheck(MACCommandAnsCheck):
    """
    Checks the answer to a DevStatusReq MAC Command previously sent.
    Expected reception: TAOK message.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ Test pass if the Activation Ok message is received without an error."""
        super().step_handler(ch, method, properties, body)
        """ Test pass if the Activation Ok message is received without an error."""
        super().step_handler(ch, method, properties, body)
        devstatusans = None
        for command in self.received_commands:
            if type(command).__name__ == "DevStatusAns":
                devstatusans = command
                break
        if devstatusans:
            if self.received_testscript_msg.parse_lorawan_message().macpayload.fport_int == 0:
                key = self.ctx_test_manager.device_under_test.loramac_params.nwkskey
            else:
                key = self.ctx_test_manager.device_under_test.loramac_params.appskey
            self.print_step_info(received_str=self.received_testscript_msg.get_printable_str(
                encryption_key=key))
        else:
            raise lorawan_errors.NoMACResponseError(
                description="Expecting a DevStatusAns message to the last DevStatusReq sent.",
                test_case=self.ctx_test_manager.tc_name,
                step_name=self.name)


class DevStatusAnsCheckFinal(DevStatusAnsCheck):
    """
    Checks the answer to a DevStatusReq MAC Command previously sent. Final step, the test case result is
    PASS in case that this step verifies the correct reception of the DevStatusAns from the DUT.
    Expected reception: TAOK message.
    Sends after check: None.
    """
    def step_handler(self, ch, method, properties, body):
        """ Test pass if the Activation Ok message is received without an error."""
        super().step_handler(ch, method, properties, body)
        self.success()


class ActokToNewChannelReq(ActokToMACCommand):
    """
    Verifies the TAOK message and sends a NewChannelReq MAC Command to configure a new channel in the DUT.
    Expected reception: TAOK message.
    Sends after check: NewChannelReq MAC Command.
    """
    def __init__(self,
                 ctx_test_manager,
                 step_name,
                 next_step,
                 freq_idx_tuple_list,
                 default_rx1_window=True,
                 piggybacked=True,
                 in_frmpayload=False):
        """
        New frequencies will be configured in the DUT using NewChannelReq MAC Commands. The desired new frequencies
        will be provided to the constructor as tuples of (frequency, index) values, with the index indicating the
        place to add the new frequency in the channel database of the DUT LoRaWAN MAC parameters.

        :param next_step: next step of the test.
        :param step_name: string representation of the step name.
        :param freq_idx_tuple_list: list of (freq, index) tuples ( e.g. [(868.1, 1), (868.3, 1), (868.5, 2)] )
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        :param piggybacked: flag to indicate if the commands should be copied in the FOpts filed of the message.
        :param in_frmpayload: flag to indicate if port 0 should be used and the commands copied in the FRMPayload.
        """
        commands = b''
        self.channel_list = freq_idx_tuple_list
        for freq, idx in self.channel_list:
            if freq == 0:
                drrange = b'\x00'
            else:
                drrange = b'\x50'
            commands += b'\07' + struct.pack('B', idx) + lorawan_parameters.get_cflist(freq)[0:3] + drrange
        super().__init__(ctx_test_manager=ctx_test_manager,
                         step_name=step_name,
                         next_step=next_step,

                         command_bytes=commands,
                         default_rx1_window=default_rx1_window,
                         piggybacked=piggybacked,
                         in_frmpayload=in_frmpayload)

    def step_handler(self, ch, method, properties, body):
        super().step_handler(ch, method, properties, body)
        for freq, idx in self.channel_list:
            if freq == 0:
                self.ctx_test_manager.device_under_test.remove_frequency(idx=idx)
            else:
                self.ctx_test_manager.device_under_test.add_frequency(freq)


class NewChannelAnsOkCheck(MACCommandAnsCheck):
    """
    Verifies the TAOK message and checks that a NewChannelAns MAC Command is sent by DUT as an answer to a previously
    sent NewChannelReq command.
    Expected reception: TAOK message.
    Sends after check: None.
    """
    def __init__(self,
                 ctx_test_manager,
                 step_name,
                 next_step,
                 number_of_ans,
                 default_rx1_window=True):
        """
        :param ctx_test_manager: Test Manager of the Test Case.
        :param step_name: string representation of the step name.
        :param next_step: next step of the test.
        :param number_of_ans: number of channels added.
        :param default_rx1_window: flag to indicate if the default behaviour should be sending downlink in RX1 (or RX2).
        """
        super().__init__(ctx_test_manager=ctx_test_manager,
                         step_name=step_name, next_step=next_step, default_rx1_window=default_rx1_window)
        self.number_of_ans = number_of_ans

    def step_handler(self, ch, method, properties, body):
        """ Test pass if the Activation Ok message is received without an error."""
        super().step_handler(ch, method, properties, body)
        correct_ans = []
        for command in self.received_commands:
            if type(command).__name__ == "NewChannelAns":
                if command.is_ok:
                    correct_ans.append(command)

        if len(correct_ans) == self.number_of_ans:
            if self.received_testscript_msg.parse_lorawan_message().macpayload.fport_int == 0:
                key = self.ctx_test_manager.device_under_test.loramac_params.nwkskey
            else:
                key = self.ctx_test_manager.device_under_test.loramac_params.appskey
            self.print_step_info(received_str=self.received_testscript_msg.get_printable_str(
                encryption_key=key))
        else:
            raise lorawan_errors.MACConfigurationExchangeError(
                description="The channel configuration was unsuccessful.",
                test_case=self.ctx_test_manager.tc_name,
                step_name=self.name)






