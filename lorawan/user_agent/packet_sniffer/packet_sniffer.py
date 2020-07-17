"""
The packet sniffer module is provided to capture the ASCII Hex dump of the LoRaWAN messages
exchanged between the DUT and the TAS. The information is displayed in a format compatible with
wireshark. Using the Agent, a user could capture this messages and process them using tools such as
test2pcap.
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
import time

import lorawan.parsing.flora_messages
import message_queueing
import utils
import parameters.message_broker as message_broker


class PacketSniffer(message_queueing.MqInterface):
    """
    Captures the traffic (uplink and downlink) by consuming the uplink and downlink routing keys on the
    message broker.
    """

    def __init__(self):
        super().__init__()

        self.declare_and_consume(queue_name='sniffer_down',
                                 routing_key=message_broker.routing_keys.toAgent+'.#',
                                 callback=self.handle_sniffer_down_msg)

        self.declare_and_consume(queue_name='sniffer_up',
                                 routing_key=message_broker.routing_keys.fromAgent+'.#',
                                 callback=self.handle_sniffer_up_msg)

    def start_sniffing(self):
        """ Starts the sniffing process."""
        self.consume_start()

    def handle_sniffer_down_msg(self, ch, method, properties, body):
        """ Handler of the donwlink messages."""
        nwk_message_down = lorawan.parsing.flora_messages.GatewayMessage(json_ttm_str=body.decode())
        phypayload = nwk_message_down.get_phypaload_bytes()
        print("# DOWNLINK, {0:10.2f}:".format(time.time()))
        print(utils.bytes_to_pcap_str(phypayload))

    def handle_sniffer_up_msg(self, ch, method, properties, body):
        """ Handler of the uplink messages."""
        nwk_message_up = lorawan.parsing.flora_messages.GatewayMessage(json_ttm_str=body.decode())
        phypayload = nwk_message_up.get_phypaload_bytes()
        print("# UPLINK, {0:10.2f}:".format(time.time()))
        print(utils.bytes_to_pcap_str(phypayload))


