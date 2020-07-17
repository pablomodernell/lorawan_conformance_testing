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

import lorawan.user_agent.bridge.udp_listener as udp_listener
import message_queueing
import lorawan.parsing.lorawan
import lorawan.parsing.gateway_forwarder
import parameters.message_broker as message_broker
from parameters.message_broker import routing_keys
from lorawan.parsing.flora_messages import GatewayMessage


class SPFBridge(message_queueing.MqInterface):
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
    VERSION = b"\x01"
    PUSH_DATA_ID = b"\x00"
    PUSH_ACK_ID = b"\x01"
    PULL_DATA_ID = b"\x02"
    PULL_RESP_ID = b"\x03"
    PULL_ACK_ID = b"\x04"

    def __init__(self):
        """
        Creates a Semtech Packet Forwarder (SPF) Bridge to handle the uplink UDP messages. It is also a consumer
        of downlink messages from the broker. The SPF Bridge is a MqInterface.
        """
        super().__init__()
        self.UDP_IP = os.environ.get('PF_IP')
        self.UDP_PORT = int(os.environ.get('PF_UDP_PORT'))
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self.UDP_IP, self.UDP_PORT))
        self.gwdladdrLock1 = udp_listener.UDPListener.create_lock()
        self.gwuladdrLock2 = udp_listener.UDPListener.create_lock()
        self._gateway_dl_addr = None
        self._gateway_ul_addr = None
        self.downlink_ready_semaphore = udp_listener.UDPListener.create_semaphore()
        self.udp_listener = udp_listener.UDPListener(self)
        self._ready_to_downlink = False
        self.last_uplink_time = None
        self.declare_and_consume(queue_name='down_nwk',
                                 routing_key=message_broker.routing_keys.toAgent+'.#',
                                 callback=self.process_dlmsg)

    @property
    def gateway_dl_addr(self):
        """ Thread safe access to the downlink address of the gateway's packet forwarder."""
        with self.gwdladdrLock1:
            retval = self._gateway_dl_addr
            return retval

    @gateway_dl_addr.setter
    def gateway_dl_addr(self, downlink_addr):
        """ Thread safe access to the downlink address of the gateway's packet forwarder."""
        with self.gwdladdrLock1:
            self._gateway_dl_addr = downlink_addr

    @property
    def gateway_ul_addr(self):
        """ Thread safe access to the uplink address of the gateway's packet forwarder."""
        with self.gwuladdrLock2:
            retval = self._gateway_ul_addr
            return retval

    @gateway_ul_addr.setter
    def gateway_ul_addr(self, uladdr):
        """ Thread safe access to the uplink address of the gateway's packet forwarder."""
        with self.gwuladdrLock2:
            self._gateway_ul_addr = uladdr

    def listen_spf(self):
        """ Starts to listen for UDP uplink messages from the gateway."""
        self.udp_listener.setDaemon(True)
        self.udp_listener.start()

    def process_dlmsg(self, ch, method, properties, body):
        """
        Downlink messages handler.
        If no PULL_DATA message was previously received from the gateway (so the downlink address is unknown), the
        message is ignored.
        """
        if self._ready_to_downlink:
            received_gw_message = GatewayMessage(body.decode())
            self.send_pull_resp(received_gw_message.get_txpk_str().encode())
            elapsed_time = time.time() - self.last_uplink_time
            msg_print = "\n\n<<<<<<<<<<<<<<<<<<<<<<<<\nTime since the last uplink: {time}\n<<<<<<<<<<<<<<<<<<<<<<<<\n"
            print(msg_print.format(time=elapsed_time))
            print("Sending DL to GW: \n{0}".format(received_gw_message.get_txpk_str().encode()))
            print(received_gw_message.get_printable_str(ignore_format_errors=True))
            print("----------<<<<<<<<<<<<<<\n----------<<<<<<<<<<<<<<\n")

        else:
            print("Agent Bridge NOT ready to downlink: waiting for a PULL_DATA message from the gateway.")

    def process_uplink_data(self):
        """
        Uplink message handler.
        When a UDP message is received with an uplink message from the gateway, it is sent to the broker using the
        right routing key.
        :return: None
        """
        data, addr = self._sock.recvfrom(1024)  # buffer size is 1024 bytes
        self.last_uplink_time = time.time()
        print("\n\n>>>>>>>>>>>>>>>>>>>>>>>>\n>>>>>>>>>>>>>>>>>>>>>>>>\n")
        # print("Printing RAW received bytes:")
        # print(data)
        # print(utils.bytes_to_text(data))
        received_msg = lorawan.parsing.gateway_forwarder.SemtechUDPMsg(data)
        print(received_msg)
        # PUSH_DATA (ID=0) received -> Send an PUSH_ACK
        if received_msg.msg_id == SPFBridge.PUSH_DATA_ID[0]:
            push_ack_bytes = data[0:3] + SPFBridge.PUSH_ACK_ID
            self.gateway_ul_addr = addr
            self.send_ulresponse_raw(push_ack_bytes)

            data_msg_list = received_msg.get_data()
            if len(data_msg_list) > 0:
                for packet in data_msg_list:
                    # packet[0]: the decoded data
                    # packet[1]: the json formatted string that contains the decoded data in it's data field.
                    self.publish(msg=packet[1],
                                 routing_key=routing_keys.fromAgent+'.gw1')
                    print("Sending UpLink: {0}\n".format(packet[1]))
                    print(lorawan.parsing.lorawan.LoRaWANMessage(packet[0]))
            received_msg.print_stats()
        # PULL_DATA (ID=2) received -> Send an PULL_ACK
        elif received_msg.msg_id == SPFBridge.PULL_DATA_ID[0]:
            pull_ack = data[0:3] + SPFBridge.PULL_ACK_ID
            self.gateway_dl_addr = addr
            if not self._ready_to_downlink:
                self._ready_to_downlink = True
                self.downlink_ready_semaphore.release()
            self.send_dl_raw(pull_ack)
        print("---------->>>>>>>>>>>>>>\n---------->>>>>>>>>>>>>>\n")

    def send_ulresponse_raw(self, ul_message):
        """
        (SPFBridge, bytes) -> (None)

        Sends a UDP message to the uplink socket of the Packet Forwarder running on the gateway.

        :param ul_message: bytes to be sent as the response to an uplink message from the
        Gateway's  Semtech Packet Forwarder.
        :return: None.
        """
        assert self._gateway_ul_addr
        self._sock.sendto(ul_message, self.gateway_ul_addr)

    def send_dl_raw(self, dl_message):
        """
        (SPFBridge, bytes) -> (None)

        Sends a downlink UDP message to the Packet Forwarder running on the gateway. The IP address must be previously
        obtained by receiving a PULL REQUEST message.

        :param dl_message: bytes to be sent to the Gateway's  Semtech Packet Forwarder.
        :return: None.
        """
        assert self._gateway_dl_addr is not None
        self._sock.sendto(dl_message, self.gateway_dl_addr)

    def send_pull_resp(self, json_bytes):
        """
        (SPFBridge, bytes) -> (None)

        Sends a message to the gateway using a PULL_RESP (Pull Response) message as defined in the Semtech
        Packet Forwarder (SPF) Protocol.

        :param json_bytes: byte sequence to be sent in the payload of a SPF PULL_RESP message.
        :return: None.
        """
        message = SPFBridge.VERSION + struct.pack('>H', random.randint(0, 2 ** 16 - 1)) + SPFBridge.PULL_RESP_ID
        self.send_dl_raw(message + json_bytes)







