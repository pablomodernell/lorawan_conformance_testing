"""
Utilities of the LoRaWAN testing.
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
import random
import lorawan.lorawan_parameters.testing
import lorawan.lorawan_parameters.general


def generate_pingpong(ping=None):
    """
    (bytes) -> (bytes, bytes)
    Generates a random ping and it's corresponding pong response. If no ping is provided
    as an argument, a random sequence is generated.
    :param ping: optional bytes sequence (bytes).
    :return: (ping, pong) tuple (tuple of bytes).
    """
    if ping is None:
        ping = lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG
        pong = lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG
        for i in range(1, random.randint(2, 17)):
            x = random.randint(0, 255)
            ping += struct.pack('B', x)
            pong += struct.pack('B', (x+1) % 256)
    else:
        pong = lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG
        for i in [ping[i:i+1] for i in range(1, len(ping))]:
            pong += struct.pack('B', (struct.unpack('B', i)[0]+1) % 256)
    return ping, pong


def get_fctrl_up_byte(adr, adrackreq, ack, foptlen):
    """
    Returns the byte of the FCtrl field of FHDR.
    :param adr: bool (True/False)
    :param adrackreq: bool (True/False)
    :param ack: bool (True/False)
    :param foptlen: int. Length of the FOpts field of FHDR.
    :return: 1 byte.
    """
    assert 0 <= foptlen <= 15
    fctrl_int = foptlen
    if adr:
        fctrl_int |= 1 << 7
    if adrackreq:
        fctrl_int |= 1 << 6
    if ack:
        fctrl_int |= 1 << 5
    return struct.pack('B', fctrl_int)


def get_fctrl_down_byte(adr, ack, fpending, foptlen):
    """
    Returns the byte of the FCtrl field of FHDR.
    :param adr: bool (True/False)
    :param fpending: bool (True/False)
    :param ack: bool (True/False)
    :param foptlen: int. Lenght of the FOpts field of FHDR.
    :return: 1 byte.
    """
    assert 0 <= foptlen <= 15
    fctrl_int = foptlen
    if adr:
        fctrl_int |= 1 << 7
    if ack:
        fctrl_int |= 1 << 5
    if fpending:
        fctrl_int |= 1 << 4
    return struct.pack('B', fctrl_int)


