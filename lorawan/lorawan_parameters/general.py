"""
This module defines the general LoRaWAN parameters used by the testing tool as defined by
the LoRaWAN specification.
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
from collections import namedtuple
import lorawan.lorawan_parameters.region_eu868 as current_region


def rx_dr_offset(initial_dr, offset):
    """
    Calculates the new data rate (DR) given an inital DR value and the offset, according to the DR used by
    the current region.
    :param initial_dr: Initial Data Rate (str, e.g. 'SF12BW125').
    :param offset: offset to be applied (int).
    :return: new data rate (str, e.g. 'SF10BW125').
    """
    new_dr_idx = get_dr(initial_dr) - offset
    return LORA_DR[max(new_dr_idx, 0)]


def get_dr(dr_str):
    """
    Gets the DR from a string (e.g. 'SF12BW125' -> 0 )
    :param dr_str: string with the datarate (e.g. 'SF12BW125').
    :return: data rate (int).
    """
    return next(int(key[-1]) for key, value in LORA_DR._asdict().items() if value == dr_str)


LORA_DR = current_region.LORA_DR
DR_OFFSET = current_region.DR_OFFSET
MIN_LORA_FREQ = current_region.MIN_LORA_FREQ


def get_min_dr(frequency):
    return current_region.get_min_dr(frequency)


def get_max_dr(frequency):
    return current_region.get_max_dr(frequency)


VALID_FREQ = current_region.VALID_FREQ
RX2_DEFAULT_FREQ = current_region.DEFAULT_SETTINGS.RX2_DEFAULT_FREQ
MAC_COMMANDS = current_region.MAC_COMMANDS

Timing = namedtuple("Timing", "RECEIVE_DELAY1 RECEIVE_DELAY2 JOIN_ACCEPT_DELAY1 JOIN_ACCEPT_DELAY2, MS_IN_SEC")
TIMING = Timing(
    RECEIVE_DELAY1=current_region.DEFAULT_SETTINGS.RECEIVE_DELAY1,
    RECEIVE_DELAY2=current_region.DEFAULT_SETTINGS.RECEIVE_DELAY2,
    JOIN_ACCEPT_DELAY1=current_region.DEFAULT_SETTINGS.JOIN_ACCEPT_DELAY1,
    JOIN_ACCEPT_DELAY2=current_region.DEFAULT_SETTINGS.JOIN_ACCEPT_DELAY2,
    MS_IN_SEC=1000000
)

FCtrl = namedtuple("FCtrl",
                   "UP_ADROFF_ADRACKOFF_ACKOFF_FOPTLEN0 \
                   UP_ADROFF_ADRACKOFF_ACKOFF_FOPTLEN1 \
                   DOWN_ADROFF_ACKOFF_FPENDOFF_FOPTLEN0 \
                   DOWN_ADROFF_ACKON_FPENDOFF_FOPTLEN0")
FCTRL = FCtrl(
    UP_ADROFF_ADRACKOFF_ACKOFF_FOPTLEN0=b'\x00',
    UP_ADROFF_ADRACKOFF_ACKOFF_FOPTLEN1=b'\x01',
    DOWN_ADROFF_ACKOFF_FPENDOFF_FOPTLEN0=b'\x00',
    DOWN_ADROFF_ACKON_FPENDOFF_FOPTLEN0=b'\x20'

)

Mhdr = namedtuple("Mhdr", "JOIN_REQUEST JOIN_ACCEPT UNCONFIRMED_UP UNCONFIRMED_DOWN \
                                        CONFIRMED_UP CONFIRMED_DOWN RFU PROPIETARY")
MHDR = Mhdr(
    JOIN_REQUEST=b'\x00',
    JOIN_ACCEPT=b'\x20',
    UNCONFIRMED_UP=b'\x40',
    UNCONFIRMED_DOWN=b'\x60',
    CONFIRMED_UP=b'\x80',
    CONFIRMED_DOWN=b'\xA0',
    RFU=b'\xC0',
    PROPIETARY=b'\xE0'
)


DLSETTINGS = current_region.DLSETTINGS


JoinAcceptRxDelay = namedtuple("JoinAcceptRxDelay", "DELAY0 DELAY1 DELAY2 DELAY3 DELAY4")
JOIN_ACCEPT_RXDELAY = JoinAcceptRxDelay(
    DELAY0=b'\x00',
    DELAY1=b'\x01',
    DELAY2=b'\x02',
    DELAY3=b'\x03',
    DELAY4=b'\x04'
)


JoinAcceptCfList = namedtuple("JoinAcceptCfList", "NO_CHANNELS TEMPLATE")
JOIN_ACCEPT_CFLIST = JoinAcceptCfList(
    NO_CHANNELS=b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    TEMPLATE=b'\x56\x84\xb8\x5e\x84\x88\x66\x84\x58\x6e\x84\x00\x92\xea\x18\x58'
)


def get_cflist(*frequencies_to_add):
    """ Converts up to 5 frequency values into a 16 byte sequence. Each frequency is passed as an argument and
     is encoded as a 24 bits unsigned integer (three octets).
     The frequency values must be provided in MHz (e.g. 868.1)"""
    return current_region.get_cflist(*frequencies_to_add)


def freq_24bits_to_mhz(freq_bytes):
    return current_region.freq_24bits_to_mhz(freq_bytes=freq_bytes)


def parse_cflist(cflist_bytes):
    return current_region.parse_cflist(cflist_bytes=cflist_bytes)
