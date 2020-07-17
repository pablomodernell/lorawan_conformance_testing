"""
User side simulator auxiliary module: end device mock session information.
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
import random
import struct

import lorawan.sessions
import lorawan.lorawan_parameters.general
import utils
import conformance_testing.test_errors as test_errors


class EndDeviceMock(lorawan.sessions.EndDevice):
    """ This is an lorawan.sessions.EndDevice that also mantains the downlink counter
        (see Test Application Protocol) and is ready to send Join Request messages and parse
        Join Accept messages to update its session information.
    """
    def __init__(self, devaddr, deveui, appkey, appskey, nwkskey):
        self.downlink_counter = 0
        super().__init__(ctx_test_tool_service=None,
                         devaddr=devaddr,
                         deveui=deveui,
                         appkey=appkey,
                         appskey=appskey,
                         nwkskey=nwkskey)

    def get_join_request(self, appeui):
        """
        Creates a Join Request message.
        :param appeui: bytes of the AppEUI
        :return: bytes of the lorawan join request (phypayload)
        """
        request_payload = appeui[::-1] + self.deveui[::-1] + self.create_devnonce()[::-1]
        mhdr_and_payload = lorawan.lorawan_parameters.general.MHDR.JOIN_REQUEST + request_payload
        mic = utils.aes128_cmac(self.appkey, mhdr_and_payload)[:4]
        return mhdr_and_payload + mic

    def create_devnonce(self):
        """
        (EndDevice) -> (bytes)
        Creates a new random device nonce to be used in a join request and keeps track of the used nonces
        in order to avoid repeating a value (join requests with repeated device nonces are ignored by the network
        to prevent from replay attacks)
        :return: int (between 0 and 2ˆ16)
        """
        nonce_int = random.randint(0, 2 ** 16 - 1)
        while nonce_int in self._used_otaa_devnonces:
            nonce_int = random.randint(0, 2 ** 16 - 1)
        devnonce = struct.pack('>H', nonce_int)
        self._used_otaa_devnonces.append(devnonce)
        return devnonce

    def parse_join_accept(self, join_accept_phypayload):
        """
        Updates the keys and the device address with the information contained in a join accept message.
        :param join_accept_phypayload: byte sequence of the Join Accept PHYPayload.
        :return:
        """
        assert join_accept_phypayload[0:1] == lorawan.lorawan_parameters.general.MHDR.JOIN_ACCEPT
        join_accept_and_mic = utils.aes128_encrypt(self.appkey, join_accept_phypayload[1:])
        received_mic = join_accept_and_mic[-4:]
        calc_mic = utils.aes128_cmac(self.appkey, join_accept_phypayload[0:1] + join_accept_and_mic[:-4])[0:4]
        if not calc_mic == received_mic:
            raise test_errors.SessionError(description="Wrong MIC in the received join accept.",
                                           test_case=None,
                                           step_name=None)
        appnonce_netid_devnonce = join_accept_and_mic[:6] + self._used_otaa_devnonces[-1][::-1]
        nwkskey = utils.aes128_encrypt(self.appkey, b'\x01' + appnonce_netid_devnonce + bytes(7))
        appskey = utils.aes128_encrypt(self.appkey, b'\x02' + appnonce_netid_devnonce + bytes(7))
        devaddr = join_accept_and_mic[9:5:-1]
        self.update_device_session(devaddr=devaddr,
                                   nwkskey=nwkskey,
                                   appskey=appskey)

