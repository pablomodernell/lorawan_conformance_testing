"""
This Module defines the main the main component of the Agent service, a bridge that listens to
UDP messages from the LoRa gateway's Packet Forwarder and encapsulates and sends them using the AMQP
protocol to the Test Application Server (TAS).
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
import os
import random
import socket
import struct
import time
import logging

import lorawan.user_agent.bridge.udp_listener as udp_listener
import message_queueing
import lorawan.parsing.lorawan
import lorawan.parsing.gateway_forwarder
import parameters.message_broker as message_broker
from parameters.message_broker import routing_keys
from lorawan.parsing.flora_messages import GatewayMessage
import lorawan.user_agent.bridge.gateway_connection_manager as gw_conn_manager

logger = logging.getLogger(__name__)

PACKET_FORWARDER_VERSION_INT = int(os.environ.get('PACKET_FORWARDER_VERSION_INT'))


class SPFBridge(object):
    """
    Semtech Packet Forwarder (SPF) Bridge.
    The Bride service running in the agent (user side) is in charge of listening to the uplink messages from the
    LoRa gateway (e.g. in the same LAN of the machine running the bridge) in order to forward them to
    the broker. The broker then will be in charge of making the messages available to the
    testing services (f-interop side).
    The Bridge is also in charge of receiving the downlink messages from the testing platform to send them to the
    user's gateway.

    The user must specify the IP and port of the gateway running the packet forwarder in the environment variables:
    - *PF_IP*
    - *PF_UDP_PORT*
    """
    VERSION = bytes([PACKET_FORWARDER_VERSION_INT])
    PUSH_DATA_ID = b"\x00"
    PUSH_ACK_ID = b"\x01"
    PULL_DATA_ID = b"\x02"
    PULL_RESP_ID = b"\x03"
    PULL_ACK_ID = b"\x04"

    def __init__(self, gw_identifier, db_config):
        """

        """
        super().__init__()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.gw_identifier = gw_identifier
        self.gateway_manager = gw_conn_manager.GatewayManager(db_config=db_config)

    @property
    def gateway_dl_addr(self):
        return self.gateway_manager.get_down_addr_tuple(gw_identifier=self.gw_identifier)

    @gateway_dl_addr.setter
    def gateway_dl_addr(self, downlink_addr):
        self.gateway_manager.store_gw_connection(gw_identifier=self.gw_identifier,
                                                 gw_ip=downlink_addr[0],
                                                 gw_down_port=downlink_addr[1])

    @property
    def gateway_ul_addr(self):
        return self.gateway_manager.get_up_addr_tuple(gw_identifier=self.gw_identifier)

    @gateway_ul_addr.setter
    def gateway_ul_addr(self, uplink_addr):
        self.gateway_manager.store_gw_connection(gw_identifier=self.gw_identifier,
                                                 gw_ip=uplink_addr[0],
                                                 gw_up_port=uplink_addr[1])


    def send_dl_raw(self, dl_message):
        """
        (SPFBridge, bytes) -> (None)

        Sends a downlink UDP message to the Packet Forwarder running on the gateway. The IP address must be previously
        obtained by receiving a PULL REQUEST message.

        :param dl_message: bytes to be sent to the Gateway's  Semtech Packet Forwarder.
        :return: None.
        """
        if self.gateway_dl_addr is not None:
            logger.info(f"Sending message to {self.gateway_dl_addr}")
            self._sock.sendto(dl_message, self.gateway_dl_addr)
        else:
            logger.error(f"Gateway {self.gw_identifier} Downlink Port unknown.")


class SPFBridgeUplink(SPFBridge):
    """
    Semtech Packet Forwarder (SPF) Bridge.
    The Bride service running in the agent (user side) is in charge of listening to the uplink messages from the
    LoRa gateway (e.g. in the same LAN of the machine running the bridge) in order to forward them to
    the broker. The broker then will be in charge of making the messages available to the
    testing services (f-interop side).
    The Bridge is also in charge of receiving the downlink messages from the testing platform to send them to the
    user's gateway.

    The user must specify the IP and port of the gateway running the packet forwarder in the environment variables:
    - *PF_IP*
    - *PF_UDP_PORT*
    """

    def __init__(self, gw_identifier, db_config):
        """
        Creates a Semtech Packet Forwarder (SPF) Bridge to handle the uplink UDP messages. It is also a consumer
        of downlink messages from the broker. The SPF Bridge is a MqInterface.
        """
        super().__init__(gw_identifier=gw_identifier, db_config=db_config)
        self.UDP_IP = os.environ.get('PF_IP')
        self.UDP_PORT = int(os.environ.get('PF_UDP_PORT'))
        self._sock.bind((self.UDP_IP, self.UDP_PORT))

        self._ready_to_downlink = False
        self.uplink_mq_interface = message_queueing.MqPublisher(
            routing_key=message_broker.routing_keys.fromAgentToScheduler)

    def listen_spf(self):
        """ Starts to listen for UDP uplink messages from the gateway."""
        while True:
            self.process_uplink_data()

    def process_uplink_data(self):
        """
        Uplink message handler.
        When a UDP message is received with an uplink message from the gateway,
        it is sent to the broker using the
        right routing key.
        :return: None
        """
        data, addr = self._sock.recvfrom(1024)  # buffer size is 1024 bytes
        logger.info("\n\n>>>>>>>>>>>>>>>>>>>>>>>>\n>>>>>>>>>>>>>>>>>>>>>>>>\n")
        # print("Printing RAW received bytes:")
        # print(data)
        # print(utils.bytes_to_text(data))
        received_msg = lorawan.parsing.gateway_forwarder.SemtechUDPMsg(data)
        logger.info(received_msg)
        # PUSH_DATA (ID=0) received -> Send an PUSH_ACK
        if received_msg.msg_id == SPFBridgeUplink.PUSH_DATA_ID[0]:
            push_ack_bytes = data[0:3] + SPFBridgeUplink.PUSH_ACK_ID
            self.gateway_ul_addr = addr

            data_msg_list = received_msg.get_data()
            if len(data_msg_list) > 0:
                for packet in data_msg_list:
                    # packet[0]: the decoded data
                    # packet[1]: the json string with the decoded data in it's data field.
                    self.uplink_mq_interface.send(data=packet[1],
                                                  routing_key=routing_keys.fromAgentToScheduler)
                    logger.info("Sending UpLink: {0}\n".format(packet[1]))
                    logger.info(lorawan.parsing.lorawan.LoRaWANMessage(packet[0]))
            self.send_ulresponse_raw(push_ack_bytes)
            received_msg.print_stats()
        # PULL_DATA (ID=2) received -> Send an PULL_ACK
        elif received_msg.msg_id == SPFBridgeUplink.PULL_DATA_ID[0]:
            pull_ack = data[0:3] + SPFBridgeUplink.PULL_ACK_ID
            self.gateway_dl_addr = addr
            self.send_dl_raw(pull_ack)
        logger.info("---------->>>>>>>>>>>>>>\n---------->>>>>>>>>>>>>>\n")

    def send_ulresponse_raw(self, ul_message):
        """
        (SPFBridge, bytes) -> (None)

        Sends a UDP message to the uplink socket of the Packet Forwarder running on the gateway.

        :param ul_message: bytes to be sent as the response to an uplink message from the
        Gateway's  Semtech Packet Forwarder.
        :return: None.
        """
        if self.gateway_ul_addr is not None:
            logger.info(f"Sending UL Response to {self.gateway_ul_addr}")
            self._sock.sendto(ul_message, self.gateway_ul_addr)
        else:
            logger.error(f"Gateway {self.gw_identifier} Uplink Port unknown.")


class SPFBridgeDownlink(SPFBridge):
    """
    Semtech Packet Forwarder (SPF) Bridge.
    The Bride service running in the agent (user side) is in charge of listening to the uplink messages from the
    LoRa gateway (e.g. in the same LAN of the machine running the bridge) in order to forward them to
    the broker. The broker then will be in charge of making the messages available to the
    testing services (f-interop side).
    The Bridge is also in charge of receiving the downlink messages from the testing platform to send them to the
    user's gateway.

    The user must specify the IP and port of the gateway running the packet forwarder in the environment variables:
    - *PF_IP*
    - *PF_UDP_PORT*
    """

    def __init__(self, gw_identifier, db_config):
        """
        Creates a Semtech Packet Forwarder (SPF) Bridge to handle the uplink UDP messages. It is also a consumer
        of downlink messages from the broker. The SPF Bridge is a MqInterface.
        """
        super().__init__(gw_identifier=gw_identifier, db_config=db_config)

        self.downlink_mq_interface = message_queueing.MqSelectConnectionInterface(
            queue_name='down_sch_nwk',
            routing_key=message_broker.routing_keys.fromSchedulerToAgent,
            on_message_callback=self.process_dlmsg
        )

    def process_dlmsg(self, body_str):
        """
        Downlink messages handler.
        If no PULL_DATA message was previously received from the gateway (so the downlink address is unknown), the
        message is ignored.
        """
        if self.gateway_dl_addr is not None:
            received_gw_message = GatewayMessage(body_str)
            self.send_pull_resp(received_gw_message.get_txpk_str().encode())
            logger.info(
                "Sending DL to GW: \n{0}".format(received_gw_message.get_txpk_str().encode()))
            logger.info(received_gw_message.get_printable_str(ignore_format_errors=True))
            logger.info("----------<<<<<<<<<<<<<<\n----------<<<<<<<<<<<<<<\n")

        else:
            logger.info(
                "Agent Bridge NOT ready to downlink: waiting for a PULL_DATA  from the gateway.")

    def send_pull_resp(self, json_bytes):
        """
        (SPFBridge, bytes) -> (None)

        Sends a message to the gateway using a PULL_RESP (Pull Response) message as defined in the Semtech
        Packet Forwarder (SPF) Protocol.

        :param json_bytes: byte sequence to be sent in the payload of a SPF PULL_RESP message.
        :return: None.
        """
        message = SPFBridgeUplink.VERSION + struct.pack(
            '>H', random.randint(0, 2 ** 16 - 1)) + SPFBridgeUplink.PULL_RESP_ID
        self.send_dl_raw(message + json_bytes)

    def start_listening_downlink(self):
        self.downlink_mq_interface.consume_start()
