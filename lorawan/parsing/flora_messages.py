"""
Testing tool messages specific of the LoRaWAN testing.
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
import base64
import json
import copy

import lorawan.lorawan_parameters.general
import lorawan.parsing.lorawan
import utils
import conformance_testing.test_errors as test_errors
import conformance_testing.testingtool_messages as test_messages


class GatewayMessage(test_messages.TestingToolMessage):
    """
    Message containing the LoRaWAN packet (PHYPayload) and the metadata (tmst, datr, freq, etc).
    The Gateway Messages are used by the testing platform in order to send the LoRaWAN messages and the metadata
    added by the gateway of the user to the different services. It preserves, among other things, the timing
    information that specifies when the LoRaWAN message was received by the gateway.
    {
        "codr": "4/5",
        "data": "",
        "datr": 'SF12BW125',
        "freq": 867.3,
        "imme": False,
        "ipol": True,
        "modu": "LORA",
        "ncrc": "true",
        "powe": 14,
        "rfch": 0,
        "size": 0,
        "tmst": 0
    }
    """
    empty_gw_msg = {
        "codr": "4/5",
        "data": "",
        "datr": lorawan.lorawan_parameters.general.LORA_DR.DR0,
        "freq": 867.3,
        "imme": False,
        "ipol": True,
        "modu": "LORA",
        "ncrc": "true",
        "powe": 14,
        "rfch": 0,
        "size": 0,
        "tmst": 0
    }

    def __init__(self, json_ttm_str=None):
        """
        (str) -> (NetworkMessage)
        :param json_ttm_str: string-json formatted.
        """
        if json_ttm_str:
            super().__init__(json_ttm_str=json_ttm_str)
        else:
            self.testingtool_msg_dict = copy.copy(GatewayMessage.empty_gw_msg)
        self.__lorawan_message = None  # To parse the LoRaWAN message only once.

    @property
    def datr(self):
        """ Data rate of the message."""
        return self.testingtool_msg_dict["datr"]

    @datr.setter
    def datr(self, datr):
        """ Data rate of the message."""
        self.testingtool_msg_dict["datr"] = datr
        # Set to None in order to force the parsing an creation of a new LoRaWANMessage object when calling
        # parse_lorawan_message method.
        self.__lorawan_message = None

    @property
    def size(self):
        """ Size of the message."""
        return self.testingtool_msg_dict["size"]

    @size.setter
    def size(self, size):
        """ Size of the message."""
        self.testingtool_msg_dict["size"] = size
        # Set to None in order to force the parsing an creation of a new LoRaWANMessage object when calling
        # parse_lorawan_message method.
        self.__lorawan_message = None

    @property
    def freq(self):
        """ Frequency of the message."""
        return self.testingtool_msg_dict["freq"]

    @freq.setter
    def freq(self, freq):
        """ Frequency of the message."""
        self.testingtool_msg_dict["freq"] = freq
        # Set to None in order to force the parsing an creation of a new LoRaWANMessage object when calling
        # parse_lorawan_message method.
        self.__lorawan_message = None

    @property
    def data(self):
        """ Base64 encodeded byte sequence of the message."""
        return self.testingtool_msg_dict["data"]

    @data.setter
    def data(self, data):
        """ Base64 encodeded byte sequence of the message."""
        self.testingtool_msg_dict["data"] = data
        # Set to None in order to force the parsing an creation of a new LoRaWANMessage object when calling
        # parse_lorawan_message method.
        self.__lorawan_message = None

    @property
    def tmst(self):
        return self.testingtool_msg_dict["tmst"]

    @tmst.setter
    def tmst(self, tmst):
        self.testingtool_msg_dict["tmst"] = tmst
        # Set to None in order to force the parsing an creation of a new LoRaWANMessage object when calling
        # parse_lorawan_message method.
        self.__lorawan_message = None

    @property
    def chan(self):
        return self.testingtool_msg_dict["chan"]

    @chan.setter
    def chan(self, chan):
        self.testingtool_msg_dict["chan"] = chan
        # Set to None in order to force the parsing an creation of a new LoRaWANMessage object when calling
        # parse_lorawan_message method.
        self.__lorawan_message = None

    @property
    def modu(self):
        return self.testingtool_msg_dict["modu"]

    @modu.setter
    def modu(self, modu):
        self.testingtool_msg_dict["modu"] = modu
        # Set to None in order to force the parsing an creation of a new LoRaWANMessage object when calling
        # parse_lorawan_message method.
        self.__lorawan_message = None

    def parse_lorawan_message(self, ignore_format_errors=False):
        """
        (NetworkMessage) -> (LoRaWANMessage)
        Parses and returns a LoRaWANMessage object from the data of the message.
        :return: Parsed LoRaWANMessage.
        """
        if not self.__lorawan_message:
            b64decoded_data = base64.b64decode(self.testingtool_msg_dict["data"])
            self.__lorawan_message = lorawan.parsing.lorawan.LoRaWANMessage(phypayload=b64decoded_data,
                                                                            ignore_format_errors=ignore_format_errors)
        return self.__lorawan_message

    def create_nwk_response_str(self,
                                phypayload,
                                delay,
                                data_rate=None,
                                datr_offset=None,
                                frequency=None):
        """
        (NetworkMessage, bytes, int) -> (str)
        Creates response network message and sets the timing to be scheduled to send with a specified delay.
        :param phypayload: byte sequence PHYPayload of the LoRaWAN message.
        :param delay: Delay in micro seconds (int), default value according to Region (e.g. EU861 dlay=1000000)
        :param data_rate: Data Rate to be used by the gateway in the downlink message (str, e.g. "SF12BW125").
        :param datr_offset: Data Rate offset when using RX1 Window.
        :param frequency: Frequency to be used by the gateway in the downlink message.
        :return: string of the dumped message, json formatted.
        """

        # one and only one of the variables data_rate or datr_offset must be specified.
        if (data_rate is not None and datr_offset is not None) or (data_rate is None and datr_offset is None):
            raise test_errors.TestingToolError("Data Rate (datr) not specified.")

        resp_metadata = copy.copy(self.empty_gw_msg)
        resp_metadata["size"] = len(phypayload)
        resp_metadata["data"] = base64.b64encode(phypayload).decode()
        resp_metadata["tmst"] = self.testingtool_msg_dict["tmst"] + delay
        resp_metadata["codr"] = self.testingtool_msg_dict["codr"]
        if data_rate is not None:
            resp_metadata["datr"] = data_rate
        elif datr_offset is not None:
            resp_metadata["datr"] = lorawan.lorawan_parameters.general.rx_dr_offset(
                initial_dr=self.testingtool_msg_dict["datr"],
                offset=datr_offset)
        else:
            raise test_errors.TestingToolError("Data Rate (datr) not specified.")
        if frequency:
            resp_metadata["freq"] = frequency
        else:
            resp_metadata["freq"] = self.testingtool_msg_dict["freq"]
        resp_metadata["modu"] = self.testingtool_msg_dict["modu"]
        return json.dumps(resp_metadata, sort_keys=True, indent=4)

    def get_phypaload_bytes(self):
        """
        Gets the PHYPayload byte secuence contained in the "data" field, after base64 decode.
        :return: byte sequence of the LoRaWAN PHYPayload.
        """
        return base64.b64decode(self.testingtool_msg_dict["data"])

    def create_appmessage_str(self, appskey):
        """
        Decrypts the FRMPayload of the message and creates an Application Message
        :param appskey: byte sequence of the Application Session Key (16 bytes).
        :return: json formatted string.
        """
        lorawan_message = self.parse_lorawan_message()
        devaddr = lorawan_message.macpayload.fhdr.devaddr_bytes
        fcnt = lorawan_message.macpayload.fhdr.get_fcnt_int()
        plain_frmpayload = utils.encrypt_ieee802154(key=appskey,
                                                    frmpayload=lorawan_message.macpayload.frmpayload_bytes,
                                                    direction=lorawan_message.mhdr.message_dir,
                                                    devaddr=devaddr,
                                                    fcnt=fcnt)
        port = lorawan_message.macpayload.fport_int
        json_app_dict = self.testingtool_msg_dict
        json_app_dict["DevAddr"] = base64.b64encode(devaddr).decode()
        json_app_dict["FCnt"] = fcnt
        json_app_dict["Dir"] = lorawan_message.mhdr.message_dir
        json_app_dict["FPort"] = port
        json_app_dict["FRMPayload"] = base64.b64encode(plain_frmpayload).decode()
        return json.dumps(json_app_dict)

    def get_txpk_str(self):
        downlink_msg_dict = dict()
        downlink_msg_dict["txpk"] = self.testingtool_msg_dict
        return json.dumps(downlink_msg_dict)

    def get_printable_str(self, encryption_key=None, ignore_format_errors=False):
        """ Creates a human readable string representation of the message."""
        lorawan_message = self.parse_lorawan_message(ignore_format_errors=ignore_format_errors)
        ret_str = "Timestamp: {}\n".format(self.testingtool_msg_dict["tmst"])
        ret_str += "Frequency: {}\n".format(self.testingtool_msg_dict["freq"])
        ret_str += "DR: {}\n".format(self.testingtool_msg_dict["datr"])
        ret_str += "Size: {}\n".format(self.testingtool_msg_dict["size"])
        ret_str += "PHYPayload: {}\n".format(utils.bytes_to_text(base64.b64decode(self.testingtool_msg_dict["data"])))
        if encryption_key:
            frmpayload_plaintext = lorawan_message.get_frmpayload_plaintext(key=encryption_key)
            ret_str += "FRMPayload plain text:\n{}\n".format(utils.bytes_to_text(frmpayload_plaintext))
        ret_str += str(lorawan_message)
        return ret_str


