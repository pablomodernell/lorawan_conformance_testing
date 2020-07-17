"""
Testing tool utilities.
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
import math
from Cryptodome.Cipher import AES
from Cryptodome.Hash import CMAC


def bytes_to_text(inbytes, sep=" "):
    """
    (bytes, str) -> (str)

    Formats a bytes sequence as a string. Each byte is separated
    by a space (by default, the separator could be specified as an argument).
    :param inbytes: byte sequence to be represented as a string.
    :param sep: string to be used as a separator.
    :return: string representation of the bytes.
    """
    return sep.join("{:02x}".format(c) for c in inbytes)


def aes128_cmac(key, message):
    """
    (bytes, bytes) -> (bytes)

    Calculates the AES128 CMAC of a message.
    :param key: 128 bit long key. (16 bytes sequence).
    :param message: byte sequence of the message.
    :return: CMAC of the message (16 bytes sequence).
    """
    assert len(key) == 16, "The key must be 128 bits long."
    cobj = CMAC.new(key, ciphermod=AES)
    cobj.update(message)
    return cobj.digest()


def aes128_encrypt(key, message):
    """
    (bytes, bytes) -> (bytes)

    Encrypts a message using AES128.
    :param key: encryption key (16 bytes sequence).
    :param message: message to be encrypted (length multiple of 128 bits).
    :return: encrypted message (bytes sequence).
    """
    assert len(key) == 16, "The key must be 128 bits long."
    assert len(message) % 16 == 0, "The length of the message must be a multiple of 128 bits."

    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(message)


def aes128_decrypt(key, cipher_text):
    """
    (bytes, bytes) -> (bytes)

    Decrypts a message using AES128.
    :param key: encryption key (16 bytes sequence).
    :param cipher_text: encrypted message (bytes sequence, length multiple of 128 bits).
    :return: decrypted message (bytes sequence).
    """
    assert len(key) % 16 == 0, "The key must be 128 bits long."
    assert len(cipher_text) % 16 == 0, "The length of the message must be a multiple of 128 bits."

    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.decrypt(cipher_text)


def __create_sblocks_ieee802154(key, payload_length, direction, devaddr, fcnt):
    """
    (bytes, bytes, int, bytes, int) -> (bytes)

    Auxiliary function used to create the S blocks of the encryption scheme, that is based on the generic algorithm
     described in IEEE 802.15.4/2006 Annex B [IEEE802154] and uses AES with a 128 bits key.
    :param key: 16 bytes sequence of the encryption key (bytes).
    :param payload_length: length of the payload (int).
    :param direction: Uplink -> 0, Downlink -> 1 (int).
    :param devaddr: device short address. LoraWAN DevAddr, 4 bytes big endian (bytes).
    :param fcnt: integer frame count corresponding to LoraWAN FCnt (int).
    :return: bytes sequence S of encrypted blocks, as described in LoraWAN specification v1.0.2 secction 4.3.3 (bytes).
    """
    fcnt_b = struct.pack('<I', fcnt)
    dir_b = struct.pack('>B', direction)
    s_blocks = b''
    numb_blocks = int(math.ceil(payload_length / 16))
    for i in range(1, numb_blocks+1):
        a_block_i = b'\x01\x00\x00\x00\x00' + dir_b + devaddr[::-1] + fcnt_b + b'\x00' + struct.pack('>B', i)
        s_blocks = s_blocks+aes128_encrypt(key, a_block_i)
    return s_blocks


def encrypt_ieee802154(key, frmpayload, direction, devaddr, fcnt):
    """
    (bytes, bytes, bytes, int, bytes, int) -> (bytes)

    Encrypts the FRMPayload of a message using the privided 128 bit long key. The encryption scheme used
    is based on the generic algorithm described in IEEE802.15.4/2006 Annex B [IEEE802154] using AES with
    a key length of 128 bits.
    :param key: 16 bytes sequence of the encryption key (bytes).
    :param frmpayload: bytes sequence of the frame payload to be encrypted (bytes).
    :param direction: Uplink -> 0, Downlink -> 1 (int).
    :param devaddr: device short address. LoraWAN DevAddr, 4 bytes big endian (bytes).
    :param fcnt: integer frame count corresponding to LoraWAN FCnt (int).
    :return: encrypted bytes sequence of the frame payload (bytes).
    """
    s_blocks = __create_sblocks_ieee802154(key=key,
                                           payload_length=len(frmpayload),
                                           direction=direction,
                                           devaddr=devaddr,
                                           fcnt=fcnt)
    assert len(s_blocks) % 16 == 0
    pld_padded = frmpayload + bytes(len(s_blocks) - len(frmpayload))
    return bytes_xor(pld_padded, s_blocks)[:len(frmpayload)]


def bytes_xor(byte_seq1, byte_seq2):
    """
    (bytes, bytes) -> (bytes)

    Do bit level XOR or two byte arrays.
    :param byte_seq1: byte sequence (bytes).
    :param byte_seq2: byte sequence (bytes).
    :return: XOR of the byte bytes sequences (bytes).
    """
    assert len(byte_seq1) == len(byte_seq2), "Bytes must be of the same length."
    parts = []
    for byte_seq1, byte_seq2 in zip(byte_seq1, byte_seq2):
        parts.append(bytes([byte_seq1 ^ byte_seq2]))
    return b''.join(parts)


def mic_rfc4493(key, msg, direction, devaddr, fcnt):
    """
    (bytes, bytes, int, bytes, int) -> (bytes)

    Calculates the Message Integrity Code of a message according to RFC 4493.
    :param key:16 bytes sequence of the encryption key (bytes).
    :param msg: bytes sequence of the message (bytes)
    :param direction: Uplink -> 0, Downlink -> 1 (int).
    :param devaddr: device short address. LoraWAN DevAddr, 4 bytes big endian (bytes).
    :param fcnt: integer frame count corresponding to LoraWAN FCnt (int).
    :return: 4 bytes sequence of the MIC (bytes).
    """
    len_msg_b = struct.pack('>B', len(msg))
    fcnt_b = struct.pack('<I', fcnt)
    direction_b = struct.pack('>B', direction)
    b0_msg = b'\x49\x00\x00\x00\x00' + direction_b + devaddr[::-1] + fcnt_b + b'\x00' + len_msg_b + msg
    return aes128_cmac(key, b0_msg)[0:4]


def bytes_to_pcap_str(frame):
    """
    (str) -> (str)

    Formats the PHY payload to prepare it to be processed by wireshark.
    This format of string should be easily converted to pcap using text2pcap utility:
    0000 00 0e b6 00 00 02 00 0e b6 00 00 01 08 00 45 00
    0010 00 28 00 00 00 00 ff 01 37 d1 c0 00 02 01 c0 00
    0020 02 02 08 00 a6 2f 00 01 00 01 48 65 6c 6c 6f 20
    0030 57 6f 72 6c 64 21

    :param frame: bytes sequence (bytes).
    :return: string representation of the bytes in hex format (str).
    """
    num_bytes = len(frame)
    nlines = num_bytes // 16
    ptext = ''
    for i in range(nlines + 1):
        ptext += "0x{:04x}".format(16 * i)[2:] + ' '
        ptext += bytes_to_text(frame[16 * i:16 * (i + 1)]) + '\n'
    ptext += "0x{:04x}".format(16 * (nlines + 1))[2:] + ' '
    ptext += bytes_to_text(frame[16 * (nlines + 1):]) + '\n'
    return ptext

