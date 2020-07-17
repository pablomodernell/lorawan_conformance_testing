"""
End Device session information.
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
import base64
import json
import random
import utils
import copy
import lorawan.lorawan_parameters.general as lorawan_parameters
import conformance_testing.test_errors as test_errors


class ChannelStructure(object):
    """ Channel structure of the LoRaWAN MAC parameters."""
    def __init__(self):
        """
        The channel structure mantains a data base with the configured frequencies.
        """
        self._channel_db = list(lorawan_parameters.MIN_LORA_FREQ)
        self._used_frequencies = [channel["freq"] for channel in self._channel_db if not channel["freq"] == 0]

    @property
    def used_frequencies(self):
        """ Updates from the channel data base and returns the list of frequencies currently used."""
        self._used_frequencies = [channel["freq"] for channel in self._channel_db if not channel["freq"] == 0]
        return self._used_frequencies

    def add_frequency(self, freq, idx=None):
        """
        Configures a new frequency to be used by the end device. If no position (index) is provided the new
        frequency is configured in the first non used index.
        :param freq: frequency to be added.
        :param idx: position in the channel structure to add the new frequency.
        :return:
        """
        if not idx:
            for i in range(len(self._channel_db)):
                if not self._channel_db[i]["mandatory"] and self._channel_db[i]["freq"] == 0:
                    idx = i
                    break
            if not idx:
                idx = len(self._channel_db) - 1

        if freq not in self.used_frequencies and not self._channel_db[idx]["mandatory"]:
            self._channel_db[idx]["freq"] = freq
            self._channel_db[idx]["min_dr"] = lorawan_parameters.get_min_dr(freq)
            self._channel_db[idx]["max_dr"] = lorawan_parameters.get_max_dr(freq)

    def remove_frequency(self, idx, freq=None):
        """
        Removes a frequency to disable its use.
        :param idx: index to be set as not used (set freq=0).
        :param freq: frequency to be disabled.
        :return:
        """
        if freq in self.used_frequencies:
            for channel in self._channel_db:
                if channel["freq"] == freq and not channel["mandatory"]:
                    channel["freq"] = 0
                    channel["min_dr"] = 0
                    channel["max_dr"] = 0
        frequency = self._channel_db[idx]["freq"]
        if idx and not self._channel_db[idx]["mandatory"] and not frequency == 0:
            self._channel_db[idx]["freq"] = 0
            self._channel_db[idx]["min_dr"] = 0
            self._channel_db[idx]["max_dr"] = 0


class LoRaMACParameters(object):
    """ LoRaWAN MAC parameters structure."""
    def __init__(self,
                 devaddr,
                 appskey,
                 nwkskey,
                 default_dr=lorawan_parameters.LORA_DR.DR5,
                 rx1_dr_offset=lorawan_parameters.DR_OFFSET.RX1_DEFAULT,
                 rx2_dr=lorawan_parameters.LORA_DR.DR0,
                 rx1_delay=lorawan_parameters.TIMING.RECEIVE_DELAY1,
                 rx2_delay=lorawan_parameters.TIMING.RECEIVE_DELAY2,
                 rx2_frequency=lorawan_parameters.RX2_DEFAULT_FREQ,
                 joinaccept_delay1=lorawan_parameters.TIMING.JOIN_ACCEPT_DELAY1,
                 joinaccept_delay2=lorawan_parameters.TIMING.JOIN_ACCEPT_DELAY2,
                 channel_struct=None):
        self.devaddr = devaddr
        self.appskey = appskey
        self.nwkskey = nwkskey
        self.default_dr = default_dr
        self._rx1_dr_offset = rx1_dr_offset
        self.rx2_dr = rx2_dr
        self._rx1_delay = rx1_delay
        self._rx2_delay = rx2_delay
        self.rx2_frequency = rx2_frequency
        self.joinaccept_delay1 = joinaccept_delay1
        self.joinaccept_delay2 = joinaccept_delay2
        if not channel_struct:
            self.channel_struct = ChannelStructure()
        else:
            self.channel_struct = channel_struct

    @property
    def rx1_delay(self):
        return self._rx1_delay

    @rx1_delay.setter
    def rx1_delay(self, rx1_delay):
        self._rx1_delay = rx1_delay
        self._rx2_delay = rx1_delay + lorawan_parameters.TIMING.MS_IN_SEC

    @property
    def rx2_delay(self):
        return self._rx2_delay

    @property
    def rx1_dr_offset(self):
        return self._rx1_dr_offset

    @rx1_dr_offset.setter
    def rx1_dr_offset(self, rx1_dr_offset):
        if rx1_dr_offset <= lorawan_parameters.DR_OFFSET.MIN:
            self._rx1_dr_offset = lorawan_parameters.DR_OFFSET.MIN
        elif rx1_dr_offset >= lorawan_parameters.DR_OFFSET.MAX:
            self._rx1_dr_offset = lorawan_parameters.DR_OFFSET.MAX
        else:
            self._rx1_dr_offset = rx1_dr_offset


class EndDevice(object):
    """
    Device Under Test (DUT) representation, it keeps the session information as well as the frame
    counters and communication lorawan_parameters.
    """

    def __init__(self, *, ctx_test_tool_service, devaddr, deveui, appkey, appskey, nwkskey):
        """
        Creates a Device Under Test representation based on the session information.
        :param devaddr: Device Address (DevAddr, 4 bytes).
        :param deveui: Device EUI (DevEUI, 8 bytes).
        :param appkey: Application Key (AppKey, 16 bytes).
        :param appskey: Application Session Key (AppSKey, 16 bytes).
        :param nwkskey: Network Session Key (NwkSKey, 16 bytes).
        """
        self.ctx_testing_tool_service = ctx_test_tool_service
        self.message_to_ack = False

        self.deveui = deveui
        self.appkey = appkey
        self.loramac_defaults = LoRaMACParameters(devaddr=devaddr,
                                                  appskey=appskey,
                                                  nwkskey=nwkskey)
        self.loramac_params = None
        self.loramac_previous_session = None
        self.set_default_loramac()

        self._fcnt_up = 0
        self._fcnt_down = 0
        self._used_otaa_appnonces = []
        self._used_otaa_devnonces = []

    def set_default_loramac(self):
        self.loramac_previous_session = copy.deepcopy(self.loramac_params)
        self.loramac_params = copy.deepcopy(self.loramac_defaults)

    @property
    def fcnt_up(self):
        return self._fcnt_up % 2 ** 16

    @fcnt_up.setter
    def fcnt_up(self, fcnt_up_value):
        self._fcnt_up = fcnt_up_value % 2 ** 16

    @property
    def fcnt_down(self):
        return self._fcnt_down % 2 ** 16

    @fcnt_down.setter
    def fcnt_down(self, fcnt_down_value):
        self._fcnt_down = fcnt_down_value % 2 ** 16

    def add_frequency(self, freq, idx=None):
        self.loramac_params.channel_struct.add_frequency(freq=freq, idx=idx)

    def remove_frequency(self, freq=None, idx=None):
        self.loramac_params.channel_struct.remove_frequency(freq=freq, idx=idx)

    def create_appnonce(self):
        """
        (EndDevice) -> (None)
        Creates a new random device nonce to be used in a join request and keeps track of the used nonces
        in order to avoid repeating a value (join requests with repeated device nonces are ignored by the network
        to prevent from replay attacks)
        :return: int (between 0 and 2ˆ16)
        """
        nonce = random.randint(0, 2 ** 24 - 1)
        while nonce in self._used_otaa_appnonces:
            nonce = random.randint(0, 2 ** 24 - 1)
        self._used_otaa_appnonces.append(nonce)
        return nonce

    def accept_join(self,
                    devnonce,
                    dlsettings=lorawan_parameters.DLSETTINGS.RX1OFFSET3_RX2DR0,
                    rxdelay=lorawan_parameters.JOIN_ACCEPT_RXDELAY.DELAY1,
                    cflist=lorawan_parameters.JOIN_ACCEPT_CFLIST.NO_CHANNELS):
        """
        Updates the session information and creates the PHYPayload of a join accept message to be sent to the DUT.

        :param devnonce: 2 bytes of the device nonce used in the join request message.
        :param dlsettings: byte of the dlsettings field (join accept)
        :param rxdelay: byte of the rxdelay field (join accept)
        :param cflist: 16 bytes with the frequency list.
        :return: bytes of the lorawan join accept message PHYPayload.
        """
        appnonce = struct.pack("<L", self.create_appnonce())[:3]
        devaddr_int = random.randint(0, 2 ** 32 - 1)
        nwkid_int = (devaddr_int & 0xfe000000) // 2 ** 25
        netid_int = (random.randint(0, 2 ** 24 - 1) & 0xffff80) | nwkid_int
        devaddr = struct.pack(">L", devaddr_int)
        netid = struct.pack(">L", netid_int)[-3:]
        appnonce_netid_devnonce = appnonce + netid[::-1] + devnonce[::-1]
        assert len(appnonce_netid_devnonce) == 8
        nwkskey = utils.aes128_encrypt(self.appkey, b'\x01' + appnonce_netid_devnonce + bytes(7))
        appskey = utils.aes128_encrypt(self.appkey, b'\x02' + appnonce_netid_devnonce + bytes(7))
        self.store_used_devnonce(devnonce)
        macpayload = appnonce + netid[::-1] + devaddr[::-1] + dlsettings + rxdelay + cflist
        mhdr_macpayload = lorawan_parameters.MHDR.JOIN_ACCEPT + macpayload
        mic = utils.aes128_cmac(self.appkey, mhdr_macpayload)[:4]

        join_accept_phypayload = (lorawan_parameters.MHDR.JOIN_ACCEPT +
                                  utils.aes128_decrypt(key=self.appkey,
                                                       cipher_text=macpayload + mic)
                                  )
        self.update_device_session(devaddr=devaddr, appskey=appskey, nwkskey=nwkskey)

        self.loramac_params.rx1_dr_offset = (int.from_bytes(dlsettings, byteorder='big') & 0x70) >> 4
        rx2_dr = (int.from_bytes(dlsettings, byteorder='big') & 0x0f)
        self.loramac_params.rx2_dr = lorawan_parameters.LORA_DR[rx2_dr]
        seconds_delay = max(1, (int.from_bytes(rxdelay, byteorder='big') & 0x0f))
        self.loramac_params.rx1_delay = seconds_delay * lorawan_parameters.TIMING.MS_IN_SEC
        for new_frequency in lorawan_parameters.parse_cflist(cflist):
            self.add_frequency(new_frequency)

        return join_accept_phypayload

    def prepare_lorawan_data(self,
                             frmpayload,
                             fport,
                             mhdr=lorawan_parameters.MHDR.UNCONFIRMED_DOWN,
                             fctr=lorawan_parameters.FCTRL.DOWN_ADROFF_ACKOFF_FPENDOFF_FOPTLEN0,
                             fopts=b'',
                             force_fcntdown_int=None):
        """
        Creates the PHYPayload of a LoRaWAN DATA message with the specified lorawan_parameters. It does the FRMPayload
        encryption and calculates de MIC using the device's keys.
        :param frmpayload: plain text of the FRMPayload (bytes)
        :param fport: frame port of the message (int)
        :param mhdr: MAC Header (1 byte)
        :param fctr: Frame control field of the Frame header (FHDR)
        :param fopts: Frame options field used to send MAC commands (0 to 15 bytes).
        :param force_fcntdown_int: Force the use of a forged downlink frame count (don't increase de downlink count).
        :return: bytes of the PHYPayload
        """
        if force_fcntdown_int:
            fcnt_down = force_fcntdown_int % 2 ** 16
        else:
            fcnt_down = self.fcnt_down
            self.fcnt_down += 1

        if self.message_to_ack and mhdr in (b'\xA0', b'\x60'):
            fctr = struct.pack('B', struct.unpack('B', fctr)[0] | 32)

        fhdr = self.loramac_params.devaddr[::-1] + fctr + struct.pack('<H', fcnt_down) + fopts
        mhdr_fhdr = mhdr + fhdr
        assert mhdr in (b'\x00', b'\x40', b'\x80', b'\x20', b'\x60', b'\xA0', b'\xC0'), "Unrecognized MHDR."
        if mhdr in (b'\x00', b'\x40', b'\x80'):
            direction = 0
        else:
            direction = 1
        if fport is not None and frmpayload is not None:
            if fport == 0:
                key = self.loramac_params.nwkskey
            else:
                key = self.loramac_params.appskey
            mac_hdr_payload = mhdr_fhdr + struct.pack('B', fport) + utils.encrypt_ieee802154(
                key=key,
                frmpayload=frmpayload,
                direction=direction,
                devaddr=self.loramac_params.devaddr,
                fcnt=fcnt_down)
        else:
            mac_hdr_payload = mhdr_fhdr
        phy_payload = mac_hdr_payload + utils.mic_rfc4493(key=self.loramac_params.nwkskey,
                                                          msg=mac_hdr_payload,
                                                          direction=direction,
                                                          devaddr=self.loramac_params.devaddr,
                                                          fcnt=fcnt_down)
        return phy_payload

    def update_device_session(self, devaddr, appskey, nwkskey):
        """
        Updates de identification of the devices corresponding to the current session. This could be used to update
        the short address (DevAddr) and session keys (AppSKey and NwkSKey) after a join-request and join-accept
        message interchange. After a session update the frame count value (FCnt) is reset.
        :param devaddr: bytes (4) of the device short address.
        :param appskey: bytes (8) of the application session key.
        :param nwkskey: bytes (8) of the network session key.
        :return: None
        """
        if not(len(appskey) == 16 and len(nwkskey) == 16 and len(devaddr) == 4):
            description_template = "Wrong session information.\nDevAddr={da}\nAppSkey={ak}\nNwkSKey={nk}\n"
            raise test_errors.SessionError(description=description_template.format(ak=appskey,
                                                                                   nk=nwkskey,
                                                                                   da=devaddr),
                                           step_name=None,
                                           test_case=None)
        self.loramac_previous_session = copy.deepcopy(self.loramac_params)
        self.loramac_params = copy.deepcopy(self.loramac_defaults)
        self.loramac_params.devaddr = devaddr
        self.loramac_params.appskey = appskey
        self.loramac_params.nwkskey = nwkskey
        self.fcnt_up = 0
        self.fcnt_down = 0

    def store_used_devnonce(self, devnonce):
        """
        (EndDevice, int) -> (None)
        Store the used device nonce to avoid repeated use of the same value and prevent replay attacks.
        :param devnonce: (int) Value to store as a used device nonce.
        :return: None
        """
        if devnonce in self._used_otaa_devnonces:
            raise test_errors.SessionError(description="Repeated devnonce in join request message. Replay detected.",
                                           test_case="TC",
                                           step_name="SN")
        self._used_otaa_devnonces.append(devnonce)

    def joinrequest_is_replay(self, devnonce):
        """
        (EndDevice, bute) -> (boolean)
        Detects if a device nonce was already used in a previous join request message in order to detect replayed
        messages.
        :param devnonce: device nonce (2 bytes, big endian)
        :return: True iif the device nonce was already used.
        """
        return devnonce in self._used_otaa_devnonces

    def get_json_repr(self):
        device_id = {
            "DevEUI": base64.b64encode(self.deveui).decode(),
            "DevAddr": base64.b64encode(self.loramac_params.devaddr).decode(),
            "AppSKey": base64.b64encode(self.loramac_params.appskey).decode(),
            "NwkSKey": base64.b64encode(self.loramac_params.nwkskey).decode()
        }
        return json.dumps(device_id)

    def __str__(self):
        retstr = ''
        retstr += "\tDevAddr: {0}\n".format(utils.bytes_to_text(self.loramac_params.devaddr))
        retstr += "\tDevEUI: {0}\n".format(utils.bytes_to_text(self.deveui))
        retstr += "\tAppSKey: {0}\n".format(utils.bytes_to_text(self.loramac_params.appskey))
        retstr += "\tNwkSKey: {0}\n".format(utils.bytes_to_text(self.loramac_params.nwkskey))
        retstr += "\tAppKey: {0}\n".format(utils.bytes_to_text(self.appkey))
        return retstr
