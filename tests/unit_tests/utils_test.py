"""
Automated testing of the utilities.
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
import utils
import lorawan.lorawan_utils
import pytest
import lorawan.lorawan_parameters.testing


class TestBytesToText(object):
    """
    Tests of the lorawan.utils.bytes_to_text utility function.
    Formats a bytes sequence as a string. Each byte is separated
    by a space (by default, the separator could be specified as an argument).
    """
    bytes_converted_default = (
        (b'abe', '61 62 65'),
        (b"\x33\xab\x00c", '33 ab 00 63'),
        (b"", "")
    )
    bytes_default_ids = ["bytes_to_text({}) -> {})".format(t[0], t[1]) for t in bytes_converted_default]

    bytes_converted_nosep = (
        (b'abe', '616265'),
        (b"\x33\xab\x00c", '33ab0063'),
        (b"", "")
    )
    bytes_nosep_ids = ["bytes_to_text({}) -> {})".format(t[0], t[1]) for t in bytes_converted_nosep]

    @pytest.mark.parametrize('bytes_to_convert, expected', bytes_converted_nosep, ids=bytes_nosep_ids)
    def test_bytes_nosep(self, bytes_to_convert, expected):
        """ Tests the utility function with no separator ('')."""
        assert utils.bytes_to_text(bytes_to_convert, "") == expected

    @pytest.mark.parametrize('bytes_to_convert,expected', bytes_converted_default, ids=bytes_default_ids)
    def test_bytes_defaultsep(self, bytes_to_convert, expected):
        """ Tests the utility function with the default separator (' ', a space)."""
        assert utils.bytes_to_text(bytes_to_convert) == expected


@pytest.mark.crypto
class TestAes128CMAC(object):
    """
    Test the implementation of the AES128 CMAC calculation.
    lorawan.utils.aes128_cmac calculates the AES128 CMAC of a message.
    """
    cmac_calculated = (
        (b'\x49\x00\x00\x00\x00\x00\x9f\x29\x28\x01\x00\x00\x00\x00\x00\x05',
         b'\xd1\xc5\x71\xe8\x2f\xfa\x68\x82\x42\x27\xbe\x60\x17\xfd\x51\x20'),
        (b'\x29\x28\x01\x00\x00\x00\x00\x00\x05',
         b'\xec\x2a\xc3\x35\x71\x4c\xe4\x31\xb0\x6f\x2a\xb0\x5e\x96\x1c\x37'),
        (b'\x49\x00\x00\x00\x00\x00\x9f',
         b'\x8c\xbc\x77\x0a\xdb\xa5\x9d\xf1\xfd\x9f\x70\xc4\x83\x79\xdb\xee'),
        (b'\x2b\x7e\x15\x16\x28\xae\xd2\xa6\xab\xf7\x15\x88\x09\xcf\x4f\x3c',
         b'\xab\x13\xc7\x64\x89\x6a\xc8\x23\x12\x47\xd5\xd2\xb1\x28\xe1\x3e'),
        (b'',
         b'\xbb\x1d\x69\x29\xe9\x59\x37\x28\x7f\xa3\x7d\x12\x9b\x75\x67\x46'),
    )

    @pytest.mark.parametrize('message, expected_cmac', cmac_calculated)
    def test_cmac_of_known_messages(self, default_test_key, message, expected_cmac):
        """ Checks the results of calculating the CMAC of known messages using a default key."""
        assert utils.aes128_cmac(default_test_key, message) == expected_cmac


@pytest.mark.crypto
class TestAes128Encrypt(object):
    """
    Tests the implementation of the AES 128 encryption.
    lorawan.utils.aes128_encrypt encrypts a message using AES128.
    """
    encrypted = (
        (b'\x49\x00\x00\x00\x00\x00\x9f\x29\x28\x01\x00\x00\x00\x00\x00\x05',
         b'f\x00\xfd\x0f\x1av\n\x92\x1a\xb1|\xb4\xe0\xa7\xdd^'),
        (b')(\x01\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00',
         b'\xcf\x19c`\x19uP.9]?\xa40\x00\xa91'),
        (b'I\x00\x00\x00\x00\x00\x9f\x00\x00\x00\x00\x00\x00\x00\x00\x00',
         b'M4\xe1\x85\xf3t:\x8b\xb7>\xa6jL\xe8\xc2\xa3'),
        (b'\x2b\x7e\x15\x16\x28\xae\xd2\xa6\xab\xf7\x15\x88\x09\xcf\x4f\x3c',
         b'\x7f5\x91\xd3o\xd5\x17\xa3{m\xe9\xe0\xdf\x93Kz'),
    )

    @pytest.mark.parametrize('plain_text, expected_encrypted', encrypted)
    def test_encrypt_known_messages(self, default_test_key, plain_text, expected_encrypted):
        """
        Tests the encryption of some known messages.
        :param default_test_key: fixture with the default key used for unit testing.
        :param plain_text: plain text to be encrypted.
        :param expected_encrypted: expected cipher result.
        :return:
        """
        assert utils.aes128_encrypt(default_test_key, plain_text) == expected_encrypted


@pytest.mark.crypto
class TestAes128Decrypt(object):
    """
    Tests the implementation of the AES 128 decryption.
    lorawan.utils.aes128_decrypt decrypts a message using AES128.
    """
    decrypted = (
        (b'f\x00\xfd\x0f\x1av\n\x92\x1a\xb1|\xb4\xe0\xa7\xdd^',
         b'\x49\x00\x00\x00\x00\x00\x9f\x29\x28\x01\x00\x00\x00\x00\x00\x05'),
        (b'\xcf\x19c`\x19uP.9]?\xa40\x00\xa91',
         b')(\x01\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00'),
        (b'M4\xe1\x85\xf3t:\x8b\xb7>\xa6jL\xe8\xc2\xa3',
         b'I\x00\x00\x00\x00\x00\x9f\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
        (b'\x7f5\x91\xd3o\xd5\x17\xa3{m\xe9\xe0\xdf\x93Kz',
         b'\x2b\x7e\x15\x16\x28\xae\xd2\xa6\xab\xf7\x15\x88\x09\xcf\x4f\x3c'),
    )

    @pytest.mark.parametrize('ciphertext, expected_plaintext', decrypted)
    def test_decrypt_known_messages(self, default_test_key, ciphertext, expected_plaintext):
        """
        Tests the decryption of some known messages.
        :param default_test_key: fixture with the default key used for unit testing.
        :param ciphertext: cipher text to be decrypted.
        :param expected_plaintext: expected plain text result.
        :return:
        """
        assert utils.aes128_decrypt(default_test_key, ciphertext) == expected_plaintext


@pytest.mark.crypto
class TestEncryptIEEE802154(object):
    """
    Tests the IEEE 802.15.4 encryption scheme implementation both for
    downlink and uplink messages.
    lorawan.utils.encrypt_ieee802154 encrypts the FRMPayload of a message using the privided 128 bit long key.
    The encryption scheme used is based on the generic algorithm described in IEEE802.15.4/2006 Annex B [IEEE802154]
    using AES with a key length of 128 bits.
    """
    frmpayload_pain_text = b'\x06\xae\x89\x84_\xee;\xd6^z\x84\xaa\xe3\x16L\x15'
    encrypted_uplink = (
        ((frmpayload_pain_text, 0, 0),
         b'\x00\x00\x00\x00\x00\x00\x00\xfe>\t\r\x05\x03\xab\x00\x00'),
        ((frmpayload_pain_text, 0, 10),
         b'k\xe7\xe0\xfe5\xd1\x8cIN\xb6\xf4;Tm\xce('),
        ((frmpayload_pain_text, 0, 2**16-1),
         b'rn\x1d\xcb\x8aA\nT3g\x85\\\x9f\x12\xf4l'),
        ((frmpayload_pain_text, 0, 2**16),
         b':\x80ZI\x1c\xbb\xf9\xfc3\x91J\xdb\xa3\x8f\xff\xbf'),
        ((frmpayload_pain_text, 0, 2 ** 32-1),
         b'\xdb\xe5c\x05\xef4F\xdb\xfd\xef\x0f\xc2\x9c\x03\xdd\xa1'),
    )

    encrypted_downlink = (
        ((frmpayload_pain_text, 1, 0),
         b'\xb0\xbc\x9el=f\x14\xcd\x12=\x1b\xa6X\xf7\xbb\x00'),
        ((frmpayload_pain_text, 1, 10),
         b'3\xd36\xb2\xf0\xc7\xa1\xe6@N\x84e\x0e\x9av\xbf'),
        ((frmpayload_pain_text, 1, 2**16-1),
         b'3A\xa6\xb9\x87vK\x1e\xd4fe\xae\x88\x80\xe2_'),
        ((frmpayload_pain_text, 1, 2**16),
         b"1\xe3'\x9b\x87Z\xa4\x12Z\xdcW\x7f\x05\x82\xa0\xb2"),
        ((frmpayload_pain_text, 1, 2 ** 32-1),
         b'\x8eY\x1e\xb0\xf41\xba>\x82,\xe1"cn\xb1V'),
    )

    @pytest.mark.parametrize('ul_args, expected', encrypted_uplink)
    def test_uplink_encryption(self, device_session_id, default_test_key, ul_args, expected):
        """
        Tests the encryption for an uplink message with known plain text as the FRMPayload,
        and using different frame count (FCnt (2 bytes) field of the FHDR).
        """
        calculated = utils.encrypt_ieee802154(key=default_test_key,
                                              frmpayload=ul_args[0],
                                              direction=ul_args[1],
                                              devaddr=device_session_id["DevAddr"],
                                              fcnt=ul_args[2])
        assert calculated == expected

    @pytest.mark.parametrize('dl_args, expected', encrypted_downlink)
    def test_downlink_encryption(self, device_session_id, default_test_key, dl_args, expected):
        """
        Tests the encryption for a downlink message with known plain text as the FRMPayload,
        and using different frame count (FCnt (2 bytes) field of the FHDR).
        """
        calculated = utils.encrypt_ieee802154(key=default_test_key,
                                              frmpayload=dl_args[0],
                                              direction=dl_args[1],
                                              devaddr=device_session_id["DevAddr"],
                                              fcnt=dl_args[2])
        assert calculated == expected


class TestBytesXor(object):
    """ Tests the bit by bit bytes xor utility function."""
    bytes_sequences = (
        ((b'\x0a\x0a', b'\xff\xff'), b'\xf5\xf5'),
        ((b'\x0a', b'\xff'), b'\xf5'),
        ((b'\xff\xff', b'\x0a\x0a'), b'\xf5\xf5'),
        ((b'\xff', b'\x0a'), b'\xf5'),
        ((b'', b''), b'')
    )

    @pytest.mark.parametrize('input_bytes, expected', bytes_sequences)
    def test_bytes_xor(self, input_bytes, expected):
        """ Tests the  xor (bit level) of two bytes."""
        assert utils.bytes_xor(input_bytes[0], input_bytes[1]) == expected


@pytest.mark.crypto
class TestMICRFC4493(object):
    """
    Tests the implementation of the Message Integrity Code calculation
    according to RFC 4493.
    """
    message = b'\x06\xae\x89\x84_\xee;\xd6^z\x84\xaa\xe3\x16L\x15'
    mic_uplink = (
        ((message, 0, 0),
         b'\x96@nB'),
        ((message, 0, 10),
         b'\x89f\xda\xe4'),
        ((message, 0, 2 ** 16 - 1),
         b'\r\xfe\x861'),
        ((message, 0, 2 ** 16),
         b'm\xca\xfd5'),
        ((message, 0, 2 ** 32 - 1),
         b'ZO}\xeb'),
    )
    mic_downlink = (
        ((message, 1, 0),
         b'}\x8d-\xc9'),
        ((message, 1, 10),
         b'\xc9\xceQ\xac'),
        ((message, 1, 2 ** 16 - 1),
         b'b\xae@+'),
        ((message, 1, 2 ** 16),
         b'\xbf\t\xd8\x12'),
        ((message, 1, 2 ** 32 - 1),
         b'\xc4z\xc4}'),
    )

    @pytest.mark.parametrize('agrs, expected_mic', mic_downlink)
    def test_downlink_mic(self, device_session_id, default_test_key, agrs, expected_mic):
        """
        Calculates the MIC of a downlink message.
        :param device_session_id: fixture with the session information.
        :param default_test_key: fixture with the default key used for unit testing.
        :param agrs:
        :param expected_mic:
        :return:
        """
        calculated = utils.mic_rfc4493(key=default_test_key,
                                       msg=agrs[0],
                                       direction=agrs[1],
                                       devaddr=device_session_id["DevAddr"],
                                       fcnt=agrs[2])
        assert calculated == expected_mic

    @pytest.mark.parametrize('args, expected_mic', mic_uplink)
    def test_uplink_mic(self, device_session_id, default_test_key, args, expected_mic):
        calculated = utils.mic_rfc4493(key=default_test_key,
                                       msg=args[0],
                                       direction=args[1],
                                       devaddr=device_session_id["DevAddr"],
                                       fcnt=args[2])
        assert calculated == expected_mic


class TestGeneratePingPong(object):
    """
    This test group test the creation of the ping pong messages.
    The lorawan.utils.generate_pingpong utility function generates a random ping and it's corresponding
    pong response. If no ping is provided as an argument, a random sequence is generated.
    """
    code = lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG
    ping_pong = (
        (code+b'\x01\xfa\x33\x00\x03\xab\xde\xaf', code+b'\x02\xfb\x34\x01\x04\xac\xdf\xb0'),
        (code+b'\xff\xff', code+b'\x00\x00'),
        (code+b'\xff\x00\x01\x7f', code+b'\x00\x01\x02\x80'),
        (code, code)
    )

    @pytest.mark.parametrize('ping, expected_pong', ping_pong)
    def test_calculate_pong(self, ping, expected_pong):
        """ Tests the pong response for given pings."""
        assert lorawan.lorawan_utils.generate_pingpong(ping)[1] == expected_pong

    def test_random_ping(self):
        """ Generates 10 random ping pong pairs."""
        for i in range(10):
            ping, pong = lorawan.lorawan_utils.generate_pingpong()
            assert len(ping) == len(pong), "Ping and Pong must be of the same lenght."
            assert ping[0:1] == pong[0:1] == lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG
            for byte_pos in range(1, len(ping)):
                assert (ping[byte_pos] + 1) % 256 == pong[byte_pos]


class TestGetFCtrlUpByte(object):
    """
    Tests the creation of the Frame Control (FCtrl) field (1 byte) of the
    FHDR based on the specification of the individual bits (adrackreq, ack, foptlen).
    """
    fctrl_up = (
        ((False, False, False, 0),
         b'\x00'),
        ((False, False, True, 0),
         b'\x20'),
        ((False, True, False, 0),
         b'\x40'),
        ((False, True, True, 0),
         b'\x60'),
        ((True, False, False, 0),
         b'\x80'),
        ((True, False, True, 0),
         b'\xa0'),
        ((True, True, False, 0),
         b'\xc0'),
        ((True, True, True, 0),
         b'\xe0'),
        ((False, False, False, 3),
         b'\x03'),
        ((False, False, True, 3),
         b'\x23'),
        ((False, True, False, 3),
         b'\x43'),
        ((False, True, True, 3),
         b'\x63'),
        ((True, False, False, 3),
         b'\x83'),
        ((True, False, True, 3),
         b'\xa3'),
        ((True, True, False, 3),
         b'\xc3'),
        ((True, True, True, 3),
         b'\xe3'),
    )

    @pytest.mark.parametrize('up_bits, expected_fctrl_byte', fctrl_up)
    def test_fctrl_up(self, up_bits, expected_fctrl_byte):
        assert lorawan.lorawan_utils.get_fctrl_up_byte(adr=up_bits[0],
                                                       adrackreq=up_bits[1],
                                                       ack=up_bits[2],
                                                       foptlen=up_bits[3]) == expected_fctrl_byte


class TestGetFCtrlDownByte(object):
    """
    Tests the creation of the Frame Control (FCtrl) field (1 byte) of the
    FHDR based on the specification of the individual bits (adrackreq, ack, foptlen).
    """
    fctrl_down = (
        ((False, False, False, 0),
         b'\x00'),
        ((False, False, True, 0),
         b'\x10'),
        ((False, True, False, 0),
         b'\x20'),
        ((False, True, True, 0),
         b'\x30'),
        ((True, False, False, 0),
         b'\x80'),
        ((True, False, True, 0),
         b'\x90'),
        ((True, True, False, 0),
         b'\xa0'),
        ((True, True, True, 0),
         b'\xb0'),
        ((False, False, False, 3),
         b'\x03'),
        ((False, False, True, 3),
         b'\x13'),
        ((False, True, False, 3),
         b'\x23'),
        ((False, True, True, 3),
         b'\x33'),
        ((True, False, False, 3),
         b'\x83'),
        ((True, False, True, 3),
         b'\x93'),
        ((True, True, False, 3),
         b'\xa3'),
        ((True, True, True, 3),
         b'\xb3'),
    )

    @pytest.mark.parametrize('down_bits, expected_fctrl_byte', fctrl_down)
    def test_fctrl_up(self, down_bits, expected_fctrl_byte):
        assert lorawan.lorawan_utils.get_fctrl_down_byte(adr=down_bits[0],
                                                         ack=down_bits[1],
                                                         fpending=down_bits[2],
                                                         foptlen=down_bits[3]) == expected_fctrl_byte
