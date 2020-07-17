"""
This modules implements the LoRaWAN message parsing.
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
import struct
import utils
import lorawan.lorawan_parameters.general
import lorawan.lorawan_conformance.lorawan_errors as lorawan_errors
import lorawan.parsing.mac_commands as mac_commands


MESSAGE_TYPES = sorted(lorawan.lorawan_parameters.general.MHDR._asdict(),
                       key=lorawan.lorawan_parameters.general.MHDR._asdict().get,
                       reverse=False)


class ConditionalRaiser(object):
    """ Class that remembers a user's option to ignore errors and avoid raising certain exceptions. Used to force
    the parsing of the message even when detecting a wrong format.
    """
    def __init__(self, ignore_format_errors=False):
        """
        :param ignore_format_errors: flag to indicate that errors in the parsed message should be ignored.
        """
        self.ignore_format_errors = ignore_format_errors

    def raise_if_not_ok(self, condition=True):
        """ Returns True if and only if the condition is True and ignore_format_errors member is False.
        :param condition: condition to be evaluated only if the ignore format flag of the class is not set.
        """
        return not self.ignore_format_errors and not condition


class LoRaWANMessage(ConditionalRaiser):
    """  Class used to parse the LoRaWAN messages from the byte sequence of the PHYPayload."""
    def __init__(self, phypayload, ignore_format_errors=False):
        """
        (LoRaWANMessage, bytes) -> (LoRaWANMessage)

        :param phypayload: byte sequence of the PHYPayload
        :param ignore_format_errors: if True, the byte sequence will be parsed to create the object
        even if an message format error is detected.
        """
        super().__init__(ignore_format_errors=ignore_format_errors)
        if not len(phypayload) >= 12:
            raise lorawan_errors.MessageFormatError(description="Wrong LoRaWAN message length, {}: {}\n".format(
                                                                            len(phypayload),
                                                                            utils.bytes_to_text(phypayload)),
                                                    step_name=None,
                                                    test_case=None)
        self.phypayload_bytes = phypayload
        self.mhdr = LoRaWANMHDR(phypayload[0:1], ignore_format_errors=self.ignore_format_errors)
        self.macpayload = LoRaWANMACPayload(phypayload[1:-4],
                                            self.mhdr.mtype_str,
                                            ignore_format_errors=self.ignore_format_errors)
        self.mic_bytes = phypayload[-4:]
        if self.macpayload.fhdr:
            self._piggybacked_commands = self.macpayload.fhdr.piggybacked_mac
        else:
            self._piggybacked_commands = None

    @property
    def piggybacked_commands(self):
        return self._piggybacked_commands

    def __str__(self):
        """ Human readable string representation of the LoRaWAN message."""
        ret_str = ''
        ret_str += "----------------------------------------------\n"
        ret_str += "PHY payload information\n"
        ret_str += "MHDR: {0}\n".format(self.mhdr)
        ret_str += "\tMessage Type: {0}\n".format(self.mhdr.mtype_str)
        ret_str += "MACPayload: {0}\n".format(utils.bytes_to_text(self.macpayload.macpayload_bytes))
        ret_str += str(self.macpayload)
        if self.piggybacked_commands:
            ret_str += "Piggybacked MAC commands:\n"
            for command in self.piggybacked_commands:
                ret_str += str(command)
        ret_str += "MIC: {0}\n".format(utils.bytes_to_text(self.mic_bytes))
        ret_str += "==============================================\n"
        return ret_str

    def calculate_mic(self, key):
        """
        Calculates the MIC of the message using the provided key.
        :param key: NwkSKey or AppSKey used to calculate the MIC of the message.
        :return: byte sequence of the MIC (4 bytes).
        """
        mhdr_macpayload = self.mhdr.mhdr_bytes + self.macpayload.macpayload_bytes
        if self.mhdr.mtype_str in ('JOIN_REQUEST',):
            return utils.aes128_cmac(key=key, message=mhdr_macpayload)[:4]
        elif self.mhdr.mtype_str in ('UNCONFIRMED_UP', 'UNCONFIRMED_DOWN', 'CONFIRMED_UP', 'CONFIRMED_DOWN'):
            return utils.mic_rfc4493(key=key,
                                     msg=mhdr_macpayload,
                                     devaddr=self.macpayload.fhdr.devaddr_bytes,
                                     direction=self.mhdr.message_dir,
                                     fcnt=self.macpayload.fhdr.get_fcnt_int())
        else:
            return None

    def get_frmpayload_plaintext(self, key):
        """  Return the FRMPayload plain text of a LoRaWAN data message when the content was encrypted used the
         provided key.

        :param key: byte sequence of the AppSKey used to encrypt the message (16 bytes).
        :return: byte sequence of the decrypted FRMPayload.
        """
        if self.mhdr.mtype_str in ('UNCONFIRMED_UP', 'UNCONFIRMED_DOWN', 'CONFIRMED_UP', 'CONFIRMED_DOWN'):
            devaddr = self.macpayload.fhdr.devaddr_bytes
            fcnt = self.macpayload.fhdr.get_fcnt_int()
            plain_frmpayload = utils.encrypt_ieee802154(key=key,
                                                        frmpayload=self.macpayload.frmpayload_bytes,
                                                        direction=self.mhdr.message_dir,
                                                        devaddr=devaddr,
                                                        fcnt=fcnt)
            return plain_frmpayload
        else:
            return None


class LoRaWANMHDR(ConditionalRaiser):
    """ Message Header (1 byte) of the LoRaWAN message."""

    def __init__(self, mhdr, ignore_format_errors=False):
        """
        (LoRaWANMHDR, bytes) -> (LoRaWANMHDR)
        :param mhdr: bytes sequence of length 1, LoRaWAN Message Header (MHDR).
        :param ignore_format_errors: if True, the byte sequence will be parsed to create the object
        even if an message format error is detected.
        """
        super().__init__(ignore_format_errors=ignore_format_errors)
        if self.raise_if_not_ok(len(mhdr) == 1):
            raise lorawan_errors.MHDRError(description="Wrong MHDR length: {}\n".format(mhdr),
                                           step_name=None,
                                           test_case=None)
        self.mhdr_bytes = mhdr[0:1]
        self._mtype_int = (int.from_bytes(self.mhdr_bytes, byteorder='big') & 0xe0) >> 5
        self.major_int = (int.from_bytes(self.mhdr_bytes, byteorder='big') & 0x03)
        self._message_dir = None

    @property
    def mtype_int(self):
        if self.raise_if_not_ok(0 <= self._mtype_int < 7):
            raise lorawan_errors.MHDRError(description="Wrong MType: {}\n".format(self.mtype_int),
                                           step_name=None,
                                           test_case=None)
        return self._mtype_int

    @property
    def mtype_str(self):
        """ Get string representation of MType"""
        return MESSAGE_TYPES[self.mtype_int]

    @property
    def message_dir(self):
        """
        Get the message direction:
            - 0 if uplink
            - 1 if downlink
        :return: 0 or 1 (int).
        """
        if not self._message_dir:
            if self.mtype_int in (0, 2, 4):
                self._message_dir = 0
            elif self.mtype_int in (1, 3, 5):
                self._message_dir = 1
            elif self.raise_if_not_ok(self.mtype_int == 6):
                raise lorawan_errors.MHDRError(description="Unknown (RFU) MType: {}\n".format(self.mtype_int),
                                               step_name=None,
                                               test_case=None)
        return self._message_dir

    def __str__(self):
        """ Get MHDR string representation in binary format."""
        return "{:08b}".format(struct.unpack('B', self.mhdr_bytes)[0])


class LoRaWANMACPayload(ConditionalRaiser):
    """ MAC Payload of a LoRaWAN message."""
    def __init__(self, macpayload, str_mtype, ignore_format_errors=False):
        """
        (LoRaWANMACPayload, bytes, str) -> (LoRaWANMACPayload)

        :param macpayload: bytes sequence of the MAC Payload of the LoRaWAN Message (MACPayload).
        :param str_mtype: string. LoRaWAN message type (MType, e.g JOIN_REQUEST, UNCONFIRMED_UP, etc.).
        """
        super().__init__(ignore_format_errors=ignore_format_errors)
        if self.raise_if_not_ok(len(macpayload) >= 7):
            raise lorawan_errors.MACPayloadError(description="Wrong MACPayload lenght: {}\n".format(macpayload),
                                                 step_name=None,
                                                 test_case=None)
        if self.raise_if_not_ok(str_mtype in MESSAGE_TYPES):
            raise lorawan_errors.MACPayloadError(description="Unknown requested MType: {}\n".format(str_mtype),
                                                 step_name=None,
                                                 test_case=None)

        self.str_mtype = str_mtype
        self.macpayload_bytes = macpayload

        self.fhdr = None  # Only y Data messages
        self.fport_int = None  # Only y Data messages
        self.frmpayload_bytes = None  # Only y Data messages

        self.appeui_bytes = None  # Only in Join Request
        self.deveui_bytes = None  # Only in Join Request
        self.devnonce_bytes = None  # Only in Join Request

        if str_mtype in ('JOIN_REQUEST',):
            if self.raise_if_not_ok(len(macpayload) == 18):
                raise lorawan_errors.MHDRError(description="Wrong MACPayload length: {}\n".format(macpayload),
                                               step_name=None,
                                               test_case=None)
            self.appeui_bytes = macpayload[7::-1]
            self.deveui_bytes = macpayload[15:7:-1]
            self.devnonce_bytes = macpayload[:-3:-1]

        elif str_mtype in ('UNCONFIRMED_UP', 'UNCONFIRMED_DOWN', 'CONFIRMED_UP', 'CONFIRMED_DOWN'):
            self.fhdr = LoRaWANFHDR(macpayload=macpayload,
                                    str_mtype=str_mtype,
                                    ignore_format_errors=self.ignore_format_errors)
            # check if there is FRMPayload
            is_frmpayload_present = (len(macpayload) - (7 + self.fhdr.fctrl.foptslen_int)) > 1
            if is_frmpayload_present:
                self.fport_int = macpayload[(7 + self.fhdr.fctrl.foptslen_int)]
                self.frmpayload_bytes = macpayload[(8 + self.fhdr.fctrl.foptslen_int):]
                if self.fport_int == 0:
                    if self.raise_if_not_ok(not self.fhdr.piggybacked_mac):
                        raise lorawan_errors.MACPiggibackedAndPort0(
                            description=""" This message should be ignored, MAC commands both "
                                        in FRMPayload and Piggibacked.""",
                            test_case=None,
                            step_name=None
                        )
            else:
                self.fport_int = None
                self.frmpayload_bytes = None

    def __str__(self):
        """ Human readable string representation."""
        ret_str = ''
        ret_str += "----------------------------------------------\n"
        if self.str_mtype in ('JOIN_REQUEST',):
            ret_str += "Join Request information\n"
            ret_str += "AppEUI: {0}\n".format(utils.bytes_to_text(self.appeui_bytes, sep=":"))
            ret_str += "DevEUI: {0}\n".format(utils.bytes_to_text(self.deveui_bytes, sep=":"))
            ret_str += "DevNonce: {0}\n".format(utils.bytes_to_text(self.devnonce_bytes, ":"))
        elif self.str_mtype in ('UNCONFIRMED_UP', 'UNCONFIRMED_DOWN', 'CONFIRMED_UP', 'CONFIRMED_DOWN'):
            ret_str += "MAC payload information\n"
            ret_str += "FHDR: {0}\n".format(utils.bytes_to_text(self.fhdr.fhdr_bytes))
            ret_str += str(self.fhdr)
            ret_str += "FPort: {0}\n".format(self.fport_int)
            if self.frmpayload_bytes:
                ret_str += "FRMPayload: {0}\n".format(utils.bytes_to_text(self.frmpayload_bytes))
            else:
                ret_str += "No FRMPayload detected.\n"
        ret_str += "==============================================\n"
        return ret_str


class LoRaWANFHDR(ConditionalRaiser):
    """ Frame Header (FHDR) of the LoRaWAN message."""
    def __init__(self, macpayload, str_mtype, ignore_format_errors=False):
        """
        (LoRaWANFHDR, bytes, str) -> (LoRaWANFHDR)

        :param macpayload: bytes sequence of the MAC Payload of the LoRaWAN Message (MACPayload).
        :param str_mtype: string. LoRaWAN message type (MType, e.g JOIN_REQUEST, UNCONFIRMED_UP, etc.).
        """
        super().__init__(ignore_format_errors=ignore_format_errors)
        if self.raise_if_not_ok(str_mtype in ('UNCONFIRMED_UP', 'UNCONFIRMED_DOWN', 'CONFIRMED_UP', 'CONFIRMED_DOWN')):
            raise lorawan_errors.FHDRError(description="Unknown MType: {}\n".format(macpayload),
                                           step_name=None,
                                           test_case=None)
        if self.raise_if_not_ok(len(macpayload) >= 7):
            raise lorawan_errors.FHDRError(description="Wrong MACPayload lenght: {}\n".format(macpayload),
                                           step_name=None,
                                           test_case=None)
        self.devaddr_bytes = macpayload[3::-1]
        self.fctrl = LoRaWANFCtrl(fctrl_bytes=macpayload[4:5],
                                  message_type=str_mtype,
                                  ignore_format_errors=self.ignore_format_errors)
        self.fcnt_bytes = macpayload[6:4:-1]
        self._piggybacked_mac = []
        if self.fctrl.foptslen_int > 0:
            self.fopts_bytes = macpayload[7:(7 + self.fctrl.foptslen_int)]
            if str_mtype in ('UNCONFIRMED_UP', 'CONFIRMED_UP'):
                direction_up = True
            else:
                direction_up = False
            self._piggybacked_mac = mac_commands.CommandCreator.parse_mac_commands(self.fopts_bytes,
                                                                                   direction_up=direction_up)
        else:
            self.fopts_bytes = None
        self.fhdr_bytes = macpayload[:(7 + self.fctrl.foptslen_int)]

    @property
    def piggybacked_mac(self):
        return self._piggybacked_mac

    def __str__(self):
        """ Human readable string representation."""
        retstr = ''
        retstr += "\tDevAddr: {0}\n".format(utils.bytes_to_text(self.devaddr_bytes))
        retstr += "\tFCtrl: {0}\n".format(self.fctrl.fctrl_binary_str())
        retstr += str(self.fctrl)
        retstr += "\tFCnt: {0} ({1})\n".format(self.get_fcnt_int(), self.fcnt_bytes)
        retstr += "\tFOpts: {0}\n".format(self.fopts_to_str())
        return retstr

    def get_fcnt_int(self):
        """
        (LoRaWANFHDR) -> (int)
        Get FCnt int value.
        """
        return struct.unpack('>h', self.fcnt_bytes)[0]

    def fopts_to_str(self):
        """
        (LoRaWANFHDR) -> (str)
        Get string repr of FOpts
        """
        if self.fopts_bytes is None:
            return None
        else:
            return utils.bytes_to_text(self.fopts_bytes)


class LoRaWANFCtrl(ConditionalRaiser):
    """ Frame Control (FCtrl) filed of the LoRaWAN data message."""
    def __init__(self, fctrl_bytes, message_type, ignore_format_errors=False):
        """
        (LoRaWANFCtrl, bytes, str) -> (LoRaWANFCtrl)
        Creates a Frame Control Object by parsing the fctr bytes of a message.
        :param fctrl_bytes: bytes of the Frame Control (FCtrl) field of the FHDR.
        :param message_type: Message type string representation (based on MType of MHDR).
        """
        super().__init__(ignore_format_errors=ignore_format_errors)
        if self.raise_if_not_ok(len(fctrl_bytes) == 1):
            raise lorawan_errors.FCtrlError(description="Wrong MACPayload lenght: {}\n".format(fctrl_bytes),
                                            step_name=None,
                                            test_case=None)
        if self.raise_if_not_ok(message_type in MESSAGE_TYPES):
            raise lorawan_errors.MACPayloadError(description="Unknown requested MType: {}\n".format(message_type),
                                                 step_name=None,
                                                 test_case=None)
        self.fctrl_bytes = fctrl_bytes[0:1]
        self._adr_int = (int.from_bytes(self.fctrl_bytes, byteorder='big') & 0x80) >> 7
        self._ack_int = (int.from_bytes(self.fctrl_bytes, byteorder='big') & 0x20) >> 5
        self.foptslen_int = (int.from_bytes(self.fctrl_bytes, byteorder='big') & 0x0f)

        self.adrackreq_int = None
        self.fpending_int = None
        if message_type in ('UNCONFIRMED_UP', 'CONFIRMED_UP'):  # If UpLink frame
            self.adrackreq_int = (int.from_bytes(fctrl_bytes, byteorder='big') & 0x40) >> 6
            self.fpending_int = None  # Only for DL frames
        elif message_type in ('UNCONFIRMED_DOWN', 'CONFIRMED_DOWN'):  # If DownLink frame
            self.adrackreq_int = None  # Only for UL frames
            self.fpending_int = (int.from_bytes(fctrl_bytes, byteorder='big') & 0x10) >> 4

    @property
    def adr_int(self):
        if self._adr_int == 1:
            return 1
        else:
            return 0

    @property
    def ack_int(self):
        if self._ack_int == 1:
            return 1
        else:
            return 0

    def __str__(self):
        """ Human readable string representation."""
        retstr = ''
        retstr += "\t\tADR: {0}\n".format(self.adr_int)
        retstr += "\t\tACK: {0}\n".format(self.ack_int)
        retstr += "\t\tADRACKReq (Only for UL): {0}\n".format(self.adrackreq_int)
        retstr += "\t\tFPending (Only for DL): {0}\n".format(self.fpending_int)
        retstr += "\t\tFOptsLen: {0}\n".format(self.foptslen_int)
        return retstr

    def fctrl_binary_str(self):
        """
        (LoRaWANFCtrl) -> (str)
        Get FCtrl string representation
        """
        return "{:08b}".format(struct.unpack('B', self.fctrl_bytes)[0])
