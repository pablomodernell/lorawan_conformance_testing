"""
User side simulator auxiliary module: message generator.
"""
#################################################################################
# MIT License
#
# Copyright (c) 2018, Pablo D. Modernell, Universitat Oberta de Catalunya (UOC),
# Universidad de la Republica Oriental del Uruguay (UdelaR).
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

import base64
import time
import struct
import logging

import lorawan.user_agent.messenger.mock_parsing
import lorawan.user_agent.messenger.mock_sessions as mock_sessions
import lorawan.sessions
import message_queueing
import lorawan.lorawan_parameters.general
import lorawan.lorawan_parameters.testing
import lorawan.parsing.lorawan
import lorawan.parsing.flora_messages
import parameters.message_broker as message_broker
import utils
import lorawan.lorawan_utils

last_sent = 0

logger = logging.getLogger(__name__)


class MessageGenerator(object):
    """
    This class mocks the end node and the gateway with the packet forwarder.
    """

    def __init__(self, device_id, testserver_appeui):
        self.node = mock_sessions.EndDeviceMock(deveui=device_id.deveui,
                                                devaddr=device_id.devaddr,
                                                appkey=device_id.appkey,
                                                appskey=device_id.appskey,
                                                nwkskey=device_id.nwkskey)
        self.testserver_appeui = testserver_appeui
        self.mqif = message_queueing.MqInterface()
        self.last_pong_request = lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG
        self.__last_freq_idx = 0

        self.mqif.declare_and_consume(queue_name='down_nwk_mock',
                                      routing_key=message_broker.routing_keys.toAgent + '.#',
                                      durable=False,
                                      auto_delete=True,
                                      callback=self.handle_nwk_down_msg)

        self.mqif.declare_and_consume(queue_name='up_nwk_mock',
                                      routing_key=message_broker.routing_keys.fromAgent + '.#',
                                      durable=False,
                                      auto_delete=True,
                                      callback=self.handle_nwk_up_msg)

        self.mqif.declare_and_consume(queue_name='mock_up_message_actok',
                                      routing_key='mock.up.message.actok',
                                      durable=False,
                                      auto_delete=True,
                                      callback=self.handle_mock_up_message_actok)

        self.mqif.declare_and_consume(queue_name='mock_up_message_pong',
                                      routing_key='mock.up.message.pong',
                                      durable=False,
                                      auto_delete=True,
                                      callback=self.handle_mock_up_message_pong)

        self.mqif.declare_and_consume(queue_name='mock_up_message_join',
                                      routing_key='mock.up.message.join',
                                      durable=False,
                                      auto_delete=True,
                                      callback=self.handle_mock_up_message_join)

        self.mqif.declare_and_consume(queue_name='mock_up_data',
                                      routing_key='mock.up.data',
                                      durable=False,
                                      auto_delete=True,
                                      callback=self.handle_mock_up_data)

        self.mqif.declare_and_consume(queue_name='mock_configure_resetABP',
                                      routing_key='mock.configure.resetABP',
                                      durable=False,
                                      auto_delete=True,
                                      callback=self.handle_mock_configure_node_resetabp)

        self.mqif.declare_and_consume(queue_name='mock_configure',
                                      routing_key='mock.configure',
                                      durable=False,
                                      auto_delete=True,
                                      callback=self.handle_mock_configure_node)

        self.mqif.declare_and_consume(queue_name='mock_configure_showinfo',
                                      routing_key='mock.configure.showinfo',
                                      durable=False,
                                      auto_delete=True,
                                      callback=self.handle_mock_configure_showinfo)

    def get_frequency(self):
        freq = self.node.loramac_params.channel_struct.used_frequencies[
            self.__last_freq_idx % len(self.node.loramac_params.channel_struct.used_frequencies)]
        self.__last_freq_idx += 1
        return freq

    def start_consuming(self):
        self.mqif.consume_start()

    def handle_mock_configure_showinfo(self, ch, method, properties, body):
        logger.info("\nNode Session Information:")
        logger.info(self.node)

    def handle_mock_configure_node_resetabp(self, ch, method, properties, body):
        logger.info("Reseting keys to the assigned for ABP.")
        self.node.set_default_loramac()

    def handle_mock_configure_node(self, ch, method, properties, body):
        logger.info("Processing configuration request")
        cli_message = lorawan.user_agent.messenger.mock_parsing.MockMessage(
            json_mockmsg_str=body.decode())
        logger.info(cli_message)
        logger.info(f"use_dr: {cli_message.use_dr}")
        logger.info(f"freq: {cli_message.freq}\n\n")
        self.node.loramac_params.rx1_dr_offset = getattr(lorawan.lorawan_parameters.general.LORA_DR,
                                                         cli_message.use_dr)
        self.node.add_frequency(cli_message.freq())

    def handle_mock_up_data(self, ch, method, properties, body):
        logger.info("Processing data message from cli.")
        cli_message = lorawan.user_agent.messenger.mock_parsing.MockMessage(
            json_mockmsg_str=body.decode())
        logger.info(cli_message)
        logger.info(f"FPort: {cli_message.fport}")
        logger.info(f"FRMPayload: {cli_message.frmpayload_bytes}\n\n")
        if cli_message.is_confirmed:
            mac_header = lorawan.lorawan_parameters.general.MHDR.CONFIRMED_UP
        else:
            mac_header = lorawan.lorawan_parameters.general.MHDR.UNCONFIRMED_UP
        self.send_to_testing_tool(
            broker_channel=ch,
            payload=cli_message.frmpayload_bytes,
            mhdr=mac_header,
            port=cli_message.fport,
            fctrl=lorawan.lorawan_utils.get_fctrl_up_byte(ack=False,
                                                          adrackreq=False,
                                                          adr=False,
                                                          foptlen=len(cli_message.fopts_bytes)),
            fopts=cli_message.fopts_bytes)

    def handle_mock_up_message_actok(self, ch, method, properties, body):
        payload = struct.pack('>H', self.node.downlink_counter)
        self.send_to_testing_tool(broker_channel=ch,
                                  payload=payload,
                                  port=224)

    def handle_mock_up_message_pong(self, ch, method, properties, body):
        pong = lorawan.lorawan_utils.generate_pingpong(ping=self.last_pong_request)[1]
        self.send_to_testing_tool(broker_channel=ch,
                                  payload=pong,
                                  port=224)
        logger.info(f"Pong sent: {utils.bytes_to_text(pong)}\n\n")

    def handle_mock_up_message_join(self, ch, method, properties, body):
        join_request = self.node.get_join_request(appeui=self.testserver_appeui)
        self.send_to_testing_tool(broker_channel=ch,
                                  payload=join_request,
                                  mhdr=lorawan.lorawan_parameters.general.MHDR.JOIN_REQUEST)
        logger.info("Join Request Sent.")
        logger.info(join_request)
        logger.info("\n\n")

    def handle_nwk_down_msg(self, ch, method, properties, body):
        n_msg = lorawan.parsing.flora_messages.GatewayMessage(json_ttm_str=body.decode())
        phypayload = n_msg.get_phypaload_bytes()
        global last_sent
        logger.info(f"\n<-<-<-\n{body.decode()}")
        logger.debug(f"Time since last uplink message sent: {time.time() - last_sent} s.")

        if phypayload[0:1] == lorawan.lorawan_parameters.general.MHDR.JOIN_ACCEPT:
            logger.info("Join accept received, updating session.")
            logger.info(
                f"\nOLD IDENTIFICATION:\n{str(self.node)}")
            self.node.parse_join_accept(phypayload)
            logger.info(
                f"\nNEW IDENTIFICATION:\n{str(self.node)}")
        else:
            lw_msg = n_msg.parse_lorawan_message(ignore_format_errors=True)
            if lw_msg.macpayload.fport_int == 0:
                key = self.node.loramac_params.nwkskey
            else:
                key = self.node.loramac_params.appskey

            rcv_pay = lw_msg.get_frmpayload_plaintext(key=key)
            # rcv_pay = utils.encrypt_ieee802154(key=self.node.loramac_params.appskey,
            #                                    frmpayload=lw_msg.macpayload.frmpayload_bytes,
            #                                    direction=1,
            #                                    devaddr=lw_msg.macpayload.fhdr.devaddr_bytes,
            #                                    fcnt=lw_msg.macpayload.fhdr.get_fcnt_int())
            # logger.info(lw_msg)
            # logger.info(f"Decrypted payload: {utils.bytes_to_text(rcv_pay)}(key: {self.node.loramac_params.appskey.hex()})")
            print_str = n_msg.get_printable_str(encryption_key=key,
                                                ignore_format_errors=True)
            logger.info(f"{print_str}")
            if lw_msg.macpayload.fport_int == 224:  # Testing message detected
                self.node.downlink_counter += 1
                if rcv_pay == lorawan.lorawan_parameters.testing.FRMPAYLOAD.TEST_ACT:
                    logger.info("Test Activation detected")
                    self.node.downlink_counter = 0
                elif rcv_pay[0:1] == lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG:
                    self.last_pong_request = rcv_pay
                    logger.info("Pong requested")
                elif rcv_pay[0:1] == lorawan.lorawan_parameters.testing.TEST_CODE.TRIGGER_JOIN:
                    logger.info(
                        "Join Request Triggered. TAS waiting for Join Request message.")

    def handle_nwk_up_msg(self, ch, method, properties, body):
        global last_sent
        last_sent = time.time()
        nwk_msg = lorawan.parsing.flora_messages.GatewayMessage(json_ttm_str=body.decode())
        phypayload = nwk_msg.get_phypaload_bytes()
        lw_msg = nwk_msg.parse_lorawan_message(ignore_format_errors=True)

        logger.info(
            f"\n->->->\nUplink: TMST: {nwk_msg.tmst}, FREQ: {nwk_msg.freq}, DATR: {nwk_msg.datr}.")

        if phypayload[0:1] == lorawan.lorawan_parameters.general.MHDR.JOIN_REQUEST:
            logger.info("Join Request detected.")
            self.node.analyze_join_request(phypayload)
            logger.info(f"Current identification:\n{str(self.node)}")
        else:
            logger.info(lw_msg)
            if lw_msg.macpayload.fport_int == 0:
                key = self.node.loramac_params.nwkskey
            else:
                key = self.node.loramac_params.appskey
            rcv_pay = lw_msg.get_frmpayload_plaintext(key=key)
            logger.info(
                f"Decrypted payload: {utils.bytes_to_text(rcv_pay)}\n(key: {self.node.loramac_params.appskey.hex()})")

            if lw_msg.macpayload.fport_int == 224:  # Testing message detected
                self.node.downlink_counter += 1
                if rcv_pay == lorawan.lorawan_parameters.testing.FRMPAYLOAD.TEST_ACT:
                    logger.info("Test Activation detected")
                    self.node.downlink_counter = 0
                elif rcv_pay[0:1] == lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG:
                    self.last_pong_request = rcv_pay
                    logger.info("Pong response")

    def send_to_testing_tool(self, broker_channel, payload,
                             port=None,
                             mhdr=lorawan.lorawan_parameters.general.MHDR.UNCONFIRMED_UP,
                             fctrl=lorawan.lorawan_parameters.general.FCTRL.UP_ADROFF_ADRACKOFF_ACKOFF_FOPTLEN0,
                             fopts=b''):
        """
        Creates a Gateway Message to send the payload to the Testing Tool. This payload could be the FRMPayload
        of a data messages (plain text to be encrypted) or a join request including the MIC and MHDR.

        PRECONDITION: In case of data messages a port must be provided.
        :param broker_channel:
        :param payload: bytes of FRMPayload in plain text for data messages and PHYPayload for Join Requests.
        :param port: int indicating the port. Must be provided for data messages.
        :param mhdr: MAC header of the message being sent.
        :param fctrl: Frame control field (FCtrl) of the frame header (FHDR).
        :param fopts: Optional frame options field (FOpts) of the frame header (FHDR).
        :return: None
        """
        logger.info("Sending message to testing tool")
        logger.info(f"FRMPayload plain text: {utils.bytes_to_text(payload)}")
        if mhdr == lorawan.lorawan_parameters.general.MHDR.JOIN_REQUEST:
            phypayload = payload
        else:
            assert port is not None
            phypayload = self.node.prepare_lorawan_data(frmpayload=payload,
                                                        fport=port,
                                                        mhdr=mhdr,
                                                        fctr=fctrl,
                                                        fopts=fopts)
        logger.info(f"PHYPayload: {utils.bytes_to_text(phypayload)}\n")
        ulmsg = lorawan.parsing.flora_messages.GatewayMessage()
        ulmsg.data = base64.b64encode(phypayload).decode()
        ulmsg.size = len(phypayload)
        ulmsg.freq = self.get_frequency()
        ulmsg.tmst = round(time.time())
        ulmsg.datr = self.node.loramac_params.default_dr
        global last_sent
        last_sent = time.time()
        logger.info(str(ulmsg))
        broker_channel.basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                     routing_key=message_broker.routing_keys.fromAgent + '.gw1',
                                     body=str(ulmsg))
