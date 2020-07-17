"""
Creation and parsing of the messages needed to communicate the Agent with the Packet Forwarder
running on the user side.
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
import json
import base64
import utils


class SemtechUDPMsg:
    """
    Semtech Packet Forwarder Protocol UDP Message parsing.
    """

    # Semtech Packet Forwarder (SPF) Message Types:
    SPF_MESSAGES = ("PUSH_DATA", "PUSH ACK", "PULL_DATA", "PULL_RESP", "PULL_ACK", "TX_ACK")

    def __init__(self, message_bytes):
        """
        (SemtechUDPMsg, bytes) -> (None)
        Parses the bytes of a received SPF messages.
        :param message_bytes: byte sequence of the SPF message.
        """
        self.protocolVer = (message_bytes[0])
        self.token = message_bytes[1:3]
        self.msg_id = message_bytes[3]
        self.spf_msg_type = SemtechUDPMsg.SPF_MESSAGES[self.msg_id]
        assert self.msg_id in (0, 1, 2, 3, 4, 5)
        self.gwid = None
        self.json_object = None
        if self.msg_id in (0, 3):  # PUSH_DATA or PULL_RESP
            self.gwid = message_bytes[4:12]
            self.json_object = json.loads(message_bytes[12:].decode())
        elif self.msg_id == 2:  # PULL_DATA
            assert len(message_bytes) == 12
            self.gwid = message_bytes[4:12]

    def __str__(self):
        """ Human readable string representation."""
        ret_str = "**********************************************\n"
        ret_str += "Packet Forwarder Protocol:\n"
        ret_str += "Protocol Ver.: {0}\n".format(self.protocolVer)
        ret_str += "Token: {0}\n".format(utils.bytes_to_text(self.token))
        ret_str += "Type of Msg.: {0}\n".format(self.spf_msg_type)
        ret_str += "Message ID: {0}\n".format(self.msg_id)
        if self.gwid is None:
            ret_str += "GW ID: {0}\n".format(self.gwid)
        else:
            ret_str += "GW ID: {0}\n".format(utils.bytes_to_text(self.gwid, ":"))
        ret_str += "JSONObject: {0}\n".format(self.json_object)
        ret_str += "**********************************************\n"
        return ret_str

    def print_stats(self):
        """
        Auxiliary method to print the statistics contained in a SPF message (if any).
        :return: None
        """
        if self.spf_msg_type == "PUSH_DATA":
            pkstats_root = self.json_object.get("stat")
            if pkstats_root is not None:
                print("Stats:")
                for statField in list(pkstats_root.keys()):
                    print(statField, ": ", pkstats_root[statField])
                print(".............................")

    def get_data(self):
        """
        (GWFMessage -> list of (bytes, str) tuples)

        Returns a list of tuples (bytes, str), each element corresponding to a received message after being
        decoded (base64)
        and the json string as a second element of the tuple.
        :return: list of tuples (bytes, str) of the received messages (already decoded, base64)
        """
        decoded_pks = []
        if self.json_object is not None:
            rx_pks = self.json_object.get("rxpk")
            if rx_pks is not None:
                for pkt in rx_pks:
                    decoded_pks.append((base64.b64decode(pkt["data"]), json.dumps(pkt)))
        return decoded_pks
