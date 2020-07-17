"""
MAC Commands parsing functionalities. This module defines the supported MAC commands.
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

import abc
import utils
import struct
import lorawan.lorawan_parameters.general as lorawan_parameters


_SUPPORTED_CID = {
    "up": {
            b"\x02": {"size": 0,
                      "comm": None},
            b"\x03": {"size": 0,
                      "comm": None},
            b"\x04": {"size": 0,
                      "comm": None},
            b"\x05": {"size": 0,
                      "comm": None},
            b"\x06": {"size": 3,
                      "comm": "DevStatusAns"},
            b"\x07": {"size": 2,
                      "comm": "NewChannelAns"},
            b"\x08": {"size": 0,
                      "comm": None},
            b"\x09": {"size": 0,
                      "comm": None},
            b"\x0A": {"size": 0,
                      "comm": None}
    },
    "down": {
            b"\x02": {"size": 0,
                      "comm": None},
            b"\x03": {"size": 0,
                      "comm": None},
            b"\x04": {"size": 0,
                      "comm": None},
            b"\x05": {"size": 0,
                      "comm": None},
            b"\x06": {"size": 1,
                      "comm": "DevStatusReq"},
            b"\x07": {"size": 6,
                      "comm": "NewChannelReq"},
            b"\x08": {"size": 0,
                      "comm": None},
            b"\x09": {"size": 0,
                      "comm": None},
            b"\x0A": {"size": 0,
                      "comm": None}
    }
}


class UnknownMACCommand(Exception):
    """ Exeption raised when trying to parse an unsupported MAC Command."""
    pass


class CommandCreator(object):
    """ This class provides a MAC command parsing Factory, returning the MAC Command object present in the
    a byte sequence.
    """
    @staticmethod
    def create_maccommand(byte_sequence, direction_up):
        """
        Parses a byte sequence identifying a CID in the first byte and returning an MAC command object and the
        remaining bytes. When a mac command is identifyed; the remaining bytes, after the parsing of the command
        content (according to the command type), is returned. If an unknown CID is detected, the method returns
        None, None.
        :param byte_sequence:
        :param direction_up: True -> uplink, False -> downlink.
        :return: MACCommand and Byte sequence of the remaining bytes if a known CID is detected.
        """
        mac_command = None
        remaining_bytes = None
        if direction_up:
            msg_dir = "up"
        else:
            msg_dir = "down"
        try:
            command_name = _SUPPORTED_CID[msg_dir][byte_sequence[0:1]]["comm"]
            command_size = _SUPPORTED_CID[msg_dir][byte_sequence[0:1]]["size"]
        except UnknownMACCommand as unknown_mac:
            pass
        else:
            if command_name:
                try:
                    mac_command = eval(command_name)(byte_sequence[:command_size])
                    remaining_bytes = byte_sequence[command_size:]
                except Exception as e:
                    raise e
        finally:
            return mac_command, remaining_bytes

    @staticmethod
    def parse_mac_commands(commands_byte_sequence, direction_up):
        """
        Parses a byte sequences returning a list of the MAC Commands objects present
        in a byte sequence.
        :param commands_byte_sequence: byte sequence with the MAC Commands to be parsed.
        :param direction_up: flag indicating if the message direction is uplink.
        :return: list of MACCommands objects.
        """
        commands_list = []
        rem_fopts_bytes = commands_byte_sequence
        while rem_fopts_bytes:
            com, rem_fopts_bytes = CommandCreator.create_maccommand(byte_sequence=rem_fopts_bytes,
                                                                    direction_up=direction_up)
            if com:
                commands_list.append(com)
        return commands_list


class MACCommand(object, metaclass=abc.ABCMeta):
    """
    Base class defining the basic attributes of all MAC Commands.
    """
    def __init__(self, mac_commands_bytes):
        self._command_bytes = mac_commands_bytes
        self.cid = mac_commands_bytes[0:1]
        self._content = mac_commands_bytes[1::]
        self.command_size = len(mac_commands_bytes)

    @abc.abstractmethod
    def update_content(self):
        """ This method updates the content of the different fields of the MAC Commands, checking that
        all fields contain the last modified values."""
        pass

    @property
    def content(self):
        self.update_content()
        return self._content

    @property
    def command_bytes(self):
        self._command_bytes = self.cid + self.content
        return self._command_bytes

    def __str__(self):
        """ Human readable string representation of the MAC Command."""
        ret_str = "{name} MAC Command.\n".format(name=type(self).__name__.split('.')[-1])
        ret_str += "Command ID (CID): 0x{cid}\n".format(cid=utils.bytes_to_text(self.cid))
        ret_str += "Size: {size}\n".format(size=self.command_size)
        ret_str += "Content: 0x{content}\n".format(content=utils.bytes_to_text(self.content, ""))
        return ret_str


class DevStatusReq(MACCommand):
    """ DevStatusReq MAC Command (downlink from network server to the end device).
    With the DevStatusReq command a network server may request status information from an
    end-device. The command has no payload.
    """
    def update_content(self):
        pass


class DevStatusAns(MACCommand):
    """ DevStatusAns MAC Command (uplink from the end device to the network server.).
    If a DevStatusReq is received by an end-device, it responds with a DevStatusAns command containing the battery
    level and the margin of the demodulation signal-to-noise ratio. Refer to the LoRaWAN specification document for
    more details.
    """
    def __init__(self, mac_commands_bytes):
        super().__init__(mac_commands_bytes=mac_commands_bytes)
        self.battery = mac_commands_bytes[1:2]
        self.margin = mac_commands_bytes[2:3]

    def update_content(self):
        """ Updates tye content of the MAC Commands bytes (to be called after modification of the fields)."""
        self._content = self.battery + self.margin

    def __str__(self):
        ret_str = super().__str__()
        ret_str += "Battery Level: 0x{bat_b}\n".format(bat_b=utils.bytes_to_text(self.battery))
        ret_str += "Margin: 0x{mar_b}\n".format(mar_b=utils.bytes_to_text(self.margin))
        return ret_str


class NewChannelReq(MACCommand):
    """
    The NewChannelReq command can be used to either modify the parameters of an existing bidirectional channel
    or to create a new one. The command sets the center frequency of the new channel and the range of uplink data
    rates usable on this channel.
    """
    def __init__(self, mac_commands_bytes):
        super().__init__(mac_commands_bytes=mac_commands_bytes)
        self.chindex = mac_commands_bytes[1:2]
        self.freq = mac_commands_bytes[2:5]
        self.drrange = mac_commands_bytes[5:6]

    def update_content(self):
        self._content = self.chindex + self.freq + self.drrange

    @property
    def maxdr(self):
        return (int.from_bytes(self.drrange, byteorder='big') & 0xf0) >> 4

    @maxdr.setter
    def maxdr(self, maxdr_int):
        self.drrange = struct.pack('B', (maxdr_int % 16) << 4 | (self.mindr % 16))

    @property
    def mindr(self):
        return int.from_bytes(self.drrange, byteorder='big') & 0x0f

    @mindr.setter
    def mindr(self, mindr_int):
        self.drrange = struct.pack('B', (self.maxdr % 16) << 4 | (mindr_int % 16))

    def __str__(self):
        ret_str = super().__str__()
        ret_str += "ChIndex: 0x{chi_b}\n".format(chi_b=utils.bytes_to_text(self.chindex))
        ret_str += "Freq: 0x{freq_b} -> {freq_mhz}\n".format(freq_b=utils.bytes_to_text(self.freq),
                                                             freq_mhz=lorawan_parameters.freq_24bits_to_mhz(
                                                                 freq_bytes=self.freq[::-1]))
        ret_str += "DrRange: 0x{dr_b}\n".format(dr_b=utils.bytes_to_text(self.drrange))
        ret_str += "Min DR: {min_dr}\n".format(min_dr=self.mindr)
        ret_str += "Max DR: {max_dr}\n".format(max_dr=self.maxdr)
        return ret_str


class NewChannelAns(MACCommand):
    """ The end-device acknowledges the reception of a NewChannelReq by sending back a NewChannelAns command.
    The payload of this message contains status information indicating if the new frequency was successfully added."""
    def __init__(self, mac_commands_bytes):
        super().__init__(mac_commands_bytes=mac_commands_bytes)
        self.status = mac_commands_bytes[1:2]

    def update_content(self):
        self._content = self.status[0:1]

    @property
    def dr_ok(self):
        return (int.from_bytes(self.status, byteorder='big') & 0x02) >> 1

    @dr_ok.setter
    def dr_ok(self, is_dr_ok_bool):
        if is_dr_ok_bool:
            if self.freq_ok:
                self.status = b'\x03'
            else:
                self.status = b'\x02'
        else:
            if self.freq_ok:
                self.status = b'\x01'
            else:
                self.status = b'\x00'

    @property
    def freq_ok(self):
        return int.from_bytes(self.status, byteorder='big') & 0x01

    @freq_ok.setter
    def freq_ok(self, is_freq_ok_bool):
        if is_freq_ok_bool:
            if self.dr_ok:
                self.status = b'\x03'
            else:
                self.status = b'\x01'
        else:
            if self.dr_ok:
                self.status = b'\x02'
            else:
                self.status = b'\x00'

    @property
    def is_ok(self):
        return self.freq_ok and self.dr_ok

    def __str__(self):
        ret_str = super().__str__()
        ret_str += "DR OK: {dr_ok}\n".format(dr_ok=self.dr_ok)
        ret_str += "Freq OK: {freq_ok}\n".format(freq_ok=self.freq_ok)
        if self.is_ok:
            ret_str += "COMMAND SUCCEEDED\n"
        else:
            ret_str += "COMMAND FAILED\n"
        return ret_str
