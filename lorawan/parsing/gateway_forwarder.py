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

    def  __init__(self, message_bytes):
        """
        (SemtechUDPMsg, bytes) -> (None)
        Parses the bytes of a received SPF messages.
        :param message_bytes: byte sequence of the SPF message.
        """
        self._message_bytes = message_bytes
        self.msg_id = message_bytes[3]
        self.spf_msg_type = SemtechUDPMsg.SPF_MESSAGES[self.msg_id]
        self.json_object = None
        if self.msg_id in (0, 3):  # PUSH_DATA, PULL_RESP
            self.json_object = json.loads(message_bytes[12:].decode())

    def __str__(self):
        """ Human readable string representation."""
        ret_str = "**********************************************\n"
        ret_str += f"Packet Forwarder Protocol: {self.spf_msg_type}\n"
        ret_str += f"{self._message_bytes[:3].hex()}-{self._message_bytes[3:]}\n"
        if self.json_object is not None:
            ret_str += f"JSONObject: {self.json_object}\n"
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
        if self.json_object is None or self.json_object.get("rxpk") is None:
            return []
        for pkt in self.json_object.get("rxpk"):
            decoded_pks.append((base64.b64decode(pkt["data"]), json.dumps(pkt)))
        return decoded_pks
