"""
Region specific parameters
LoRaWAN 1.0.2 Regional Parameters
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

import collections
import struct


# 2.1.2 EU863-870 ISM Band channel frequencies
# The network channels can be freely attributed by the network operator. However the three
# following default channels must be implemented in every EU868MHz end-device. Those
# channels are the minimum set that all network gateways should always be listening on.
MIN_LORA_FREQ = ({"freq": 868.1, "max_dr": 5, "min_dr": 0, "mandatory": True},
                 {"freq": 868.3, "max_dr": 5, "min_dr": 0, "mandatory": True},
                 {"freq": 868.5, "max_dr": 5, "min_dr": 0, "mandatory": True},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False},
                 {"freq": 0, "max_dr": 0, "min_dr": 0, "mandatory": False})

VALID_FREQ = [(8631+2*i)/10 for i in range(0, 28)] + [869.525, 869.850] + [(8701+2*i)/10 for i in range(0, 15)]


def get_min_dr(frequency):
    """ Returns the MIN data rate for the provided frequency."""
    # if frequency in VALID_FREQ:
    #     return 0
    # else:
    #     return 0
    return 0


def get_max_dr(frequency):
    """ Returns the MAX data rate for the provided frequency."""
    if frequency in VALID_FREQ:
        return 5
    else:
        return 0


# 2.1.3 EU863-870 Data Rate and End-device Output Power encoding
LoraDr = collections.namedtuple("LoraDr", "DR0 DR1 DR2 DR3 DR4 DR5 DR6")
LORA_DR = LoraDr(
    DR0='SF12BW125',
    DR1='SF11BW125',
    DR2='SF10BW125',
    DR3='SF9BW125',
    DR4='SF8BW125',
    DR5='SF7BW125',
    DR6='SF7BW250'
)

DrOffset = collections.namedtuple("DrOffset", "MIN MAX RX1_DEFAULT")
DR_OFFSET = DrOffset(
    MIN=0,
    MAX=5,
    RX1_DEFAULT=0
)

# 2.1.7 EU863-870 Receive windows
# The RX1 receive window uses the same channel than the preceding uplink. The data rate is
# a function of the uplink data rate and the RX1DROffset as given by the following table. The
# allowed values for RX1DROffset are in the [0:5] range. Values in the [6:7] range are reserved
# for future use.
# The RX2 receive window uses a fixed frequency and data rate. The default lorawan_parameters are
# 869.525 MHz / DR0 (SF12, 125 kHz)
JoinAcceptDlSettings = collections.namedtuple("JoinAcceptDlSettings",
                                              "RX1OFFSET0_RX2DR0 \
                                              RX1OFFSET1_RX2DR0 \
                                              RX1OFFSET2_RX2DR0 \
                                              RX1OFFSET3_RX2DR0 \
                                              RX1OFFSET4_RX2DR0 \
                                              RX1OFFSET5_RX2DR0 \
                                              RX1OFFSET0_RX2DR1 \
                                              RX1OFFSET1_RX2DR1 \
                                              RX1OFFSET2_RX2DR1 \
                                              RX1OFFSET3_RX2DR1 \
                                              RX1OFFSET4_RX2DR1 \
                                              RX1OFFSET5_RX2DR1 \
                                              RX1OFFSET0_RX2DR2 \
                                              RX1OFFSET1_RX2DR2 \
                                              RX1OFFSET2_RX2DR2 \
                                              RX1OFFSET3_RX2DR2 \
                                              RX1OFFSET4_RX2DR2 \
                                              RX1OFFSET5_RX2DR2 \
                                              RX1OFFSET0_RX2DR3 \
                                              RX1OFFSET1_RX2DR3 \
                                              RX1OFFSET2_RX2DR3 \
                                              RX1OFFSET3_RX2DR3 \
                                              RX1OFFSET4_RX2DR3 \
                                              RX1OFFSET5_RX2DR3"
                                              )
DLSETTINGS = JoinAcceptDlSettings(
    RX1OFFSET0_RX2DR0=b'\x00',
    RX1OFFSET1_RX2DR0=b'\x10',
    RX1OFFSET2_RX2DR0=b'\x20',
    RX1OFFSET3_RX2DR0=b'\x30',
    RX1OFFSET4_RX2DR0=b'\x40',
    RX1OFFSET5_RX2DR0=b'\x50',
    RX1OFFSET0_RX2DR1=b'\x01',
    RX1OFFSET1_RX2DR1=b'\x11',
    RX1OFFSET2_RX2DR1=b'\x21',
    RX1OFFSET3_RX2DR1=b'\x31',
    RX1OFFSET4_RX2DR1=b'\x41',
    RX1OFFSET5_RX2DR1=b'\x51',
    RX1OFFSET0_RX2DR2=b'\x02',
    RX1OFFSET1_RX2DR2=b'\x12',
    RX1OFFSET2_RX2DR2=b'\x22',
    RX1OFFSET3_RX2DR2=b'\x32',
    RX1OFFSET4_RX2DR2=b'\x42',
    RX1OFFSET5_RX2DR2=b'\x52',
    RX1OFFSET0_RX2DR3=b'\x03',
    RX1OFFSET1_RX2DR3=b'\x13',
    RX1OFFSET2_RX2DR3=b'\x23',
    RX1OFFSET3_RX2DR3=b'\x33',
    RX1OFFSET4_RX2DR3=b'\x43',
    RX1OFFSET5_RX2DR3=b'\x53'
)

# 2.1.9 EU863-870 Default Settings
# If the actual parameter values implemented in the end-device are different from those default
# values (for example the end-device uses a longer RECEIVE_DELAY1 and
# RECEIVE_DELAY2 latency), those lorawan_parameters must be communicated to the network server
# using an out-of-band channel during the end-device commissioning process. The network
# server may not accept lorawan_parameters different from those default values.

# 5 EU863-870 MAC Commands
#
MacCommands = collections.namedtuple("MacCommands",
                                     "LinkADRReq \
                                     DevStatusReq")
MAC_COMMANDS = MacCommands(
    LinkADRReq=b'\x03',
    DevStatusReq=b'\x06'
)


Default = collections.namedtuple("Default", "RECEIVE_DELAY1 RECEIVE_DELAY2 JOIN_ACCEPT_DELAY1 \
                                JOIN_ACCEPT_DELAY2 MAX_FCNT_GAP ADR_ACK_LIMIT ADR_ACK_DELAY ACK_TIMEOUT \
                                RX2_DEFAULT_FREQ")
DEFAULT_SETTINGS = Default(
    RECEIVE_DELAY1=1000000,
    RECEIVE_DELAY2=2000000,
    JOIN_ACCEPT_DELAY1=5000000,
    JOIN_ACCEPT_DELAY2=6000000,
    MAX_FCNT_GAP=16384,
    ADR_ACK_LIMIT=64,
    ADR_ACK_DELAY=32,
    ACK_TIMEOUT=2000000,
    RX2_DEFAULT_FREQ=869.525
)


def get_cflist(*frequencies_to_add):
    """ Converts up to 5 frequency values into a 16 byte sequence. Each frequency is passed as an argument and
     is encoded as a 24 bits unsigned integer (three octets). All this channels have to be usable for DR0 to DR5
     125kHz LoRa modulation. The frequency values must be provided in MHz (e.g. 868.1)."""
    cflist = b''
    assert 0 <= len(frequencies_to_add) <= 5
    for frequency in frequencies_to_add:
        if frequency in VALID_FREQ:
            #  cflist += struct.pack('>BH', *(divmod(int(frequency * 10000), 1 << 16)))
            cflist += struct.pack('<BH', *(divmod(int(frequency*10000), 1 << 8)[::-1]))
        else:
            cflist += b'\x00\x00\x00'
    cflist += bytes(16-len(frequencies_to_add)*3)
    return cflist


def freq_24bits_to_mhz(freq_bytes):
    return struct.unpack(">I", b'\x00' + freq_bytes[::-1])[0] / 10000


def parse_cflist(cflist_bytes):
    assert len(cflist_bytes) == 16
    # return [struct.unpack(">I", b'\x00' + cflist_bytes[3 * i:3 * i + 3])[0] / 10000 for i in range(0, 5) if
    #  not cflist_bytes[3 * i:3 * i + 3] == b'\x00\x00\x00']
    return [struct.unpack(">I", b'\x00' + cflist_bytes[3 * i:3 * i + 3][::-1])[0] / 10000 for i in range(0, 5) if
            not cflist_bytes[3 * i:3 * i + 3] == b'\x00\x00\x00']

