import struct
import random
import utils
import downlink_scheduler_tool.scheduler_errors as scheduler_errors
import downlink_scheduler_tool.devices_data as dev_data
import lorawan.lorawan_parameters.general as lorawan_parameters

import logging

logger = logging.getLogger(__name__)


class DeviceSession(object):
    def __init__(self, dev_eui, appkey, dev_addr=None, app_s_key=None, nwk_s_key=None, fcnt_down=0):
        self.dev_eui = dev_eui
        self.appkey = appkey
        self.dev_addr = dev_addr
        self.app_s_key = app_s_key
        self.nwk_s_key = nwk_s_key
        self.fcnt_down = fcnt_down

        self._used_otaa_appnonces = []
        self._used_otaa_devnonces = []

        self.default_dr = lorawan_parameters.LORA_DR.DR5,
        self.rx1_dr_offset = lorawan_parameters.DR_OFFSET.RX1_DEFAULT,
        self.rx2_dr = lorawan_parameters.LORA_DR.DR0,
        self.rx1_delay = lorawan_parameters.TIMING.RECEIVE_DELAY1,
        self.rx2_delay = lorawan_parameters.TIMING.RECEIVE_DELAY2,
        self.rx2_frequency = lorawan_parameters.RX2_DEFAULT_FREQ,
        self.joinaccept_delay1 = lorawan_parameters.TIMING.JOIN_ACCEPT_DELAY1,
        self.joinaccept_delay2 = lorawan_parameters.TIMING.JOIN_ACCEPT_DELAY2

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

    def store_used_devnonce(self, devnonce):
        """
        (EndDevice, int) -> (None)
        Store the used device nonce to avoid repeated use of the same value and prevent replay attacks.
        :param devnonce: (int) Value to store as a used device nonce.
        :return: None
        """
        if devnonce in self._used_otaa_devnonces:
            raise scheduler_errors.DuplicatedNonce()
        self._used_otaa_devnonces.append(devnonce)

    def accept_join(self, devnonce, dlsettings, rxdelay, cflist):
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

        nwkskey = utils.aes128_encrypt(self.appkey, b'\x01' + appnonce_netid_devnonce + bytes(7))
        appskey = utils.aes128_encrypt(self.appkey, b'\x02' + appnonce_netid_devnonce + bytes(7))
        logger.info(f"AppSKey: {utils.bytes_to_text(appskey)}")
        logger.info(f"NwkSKey: {utils.bytes_to_text(nwkskey)}")
        self.store_used_devnonce(devnonce)
        macpayload = appnonce + netid[::-1] + devaddr[::-1] + dlsettings + rxdelay + cflist
        mhdr_macpayload = lorawan_parameters.MHDR.JOIN_ACCEPT + macpayload
        mic = utils.aes128_cmac(self.appkey, mhdr_macpayload)[:4]

        join_accept_phypayload = (lorawan_parameters.MHDR.JOIN_ACCEPT +
                                  utils.aes128_decrypt(key=self.appkey,
                                                       cipher_text=macpayload + mic)
                                  )
        self.update_device_session(devaddr=devaddr, appskey=appskey, nwkskey=nwkskey)

        self.rx1_dr_offset = (int.from_bytes(dlsettings, byteorder='big') & 0x70) >> 4
        rx2_dr = (int.from_bytes(dlsettings, byteorder='big') & 0x0f)
        self.rx2_dr = lorawan_parameters.LORA_DR[rx2_dr]
        seconds_delay = max(1, (int.from_bytes(rxdelay, byteorder='big') & 0x0f))
        self.rx1_delay = seconds_delay * lorawan_parameters.TIMING.MS_IN_SEC

        return join_accept_phypayload

    def update_device_session(self, devaddr, appskey, nwkskey):
        self.dev_addr = devaddr
        self.app_s_key = appskey
        self.nwk_s_key = nwkskey

    def prepare_lorawan_data(self,
                             frmpayload,
                             fport=1,
                             mhdr=lorawan_parameters.MHDR.UNCONFIRMED_DOWN,
                             fctr=lorawan_parameters.FCTRL.DOWN_ADROFF_ACKOFF_FPENDOFF_FOPTLEN0,
                             fopts=b''):
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
        fcnt_down = 0

        fhdr = self.dev_addr[::-1] + fctr + struct.pack('<H', fcnt_down) + fopts
        mhdr_fhdr = mhdr + fhdr
        assert mhdr in (
        b'\x00', b'\x40', b'\x80', b'\x20', b'\x60', b'\xA0', b'\xC0'), "Unrecognized MHDR."
        if mhdr in (b'\x00', b'\x40', b'\x80'):
            direction = 0
        else:
            direction = 1
        if fport is not None and frmpayload is not None:
            if fport == 0:
                key = self.nwk_s_key
            else:
                key = self.app_s_key
            mac_hdr_payload = mhdr_fhdr + struct.pack('B', fport) + utils.encrypt_ieee802154(
                key=key,
                frmpayload=frmpayload,
                direction=direction,
                devaddr=self.dev_addr,
                fcnt=fcnt_down)
        else:
            mac_hdr_payload = mhdr_fhdr
        phy_payload = mac_hdr_payload + utils.mic_rfc4493(key=self.nwk_s_key,
                                                          msg=mac_hdr_payload,
                                                          direction=direction,
                                                          devaddr=self.dev_addr,
                                                          fcnt=fcnt_down)
        return phy_payload


class DevicesSessionHandler(object):
    def __init__(self):
        self._devices = dev_data.devices_to_configure
        self._active_sessions = {}

    def is_registered(self, dev_eui_hex, app_eui_hex=None):
        if dev_eui_hex not in self._devices:
            return False 
        if not app_eui_hex or "appeui" not in self._devices[dev_eui_hex]:
            return True 
        return self._devices[dev_eui_hex]["appeui"] == app_eui_hex

    def has_active_session(self, dev_eui_hex):
        return dev_eui_hex in self._active_sessions

    def get_appkey_hex(self, dev_eui_hex):
        if self.is_registered(dev_eui_hex=dev_eui_hex):
            return self._devices[dev_eui_hex]["appkey"]

    def get_command_hex(self, dev_addr_hex):
        dev_eui_hex = self.get_dev_eui_hex(dev_addr_hex=dev_addr_hex)
        if self.is_registered(dev_eui_hex=dev_eui_hex):
            return self._devices[dev_eui_hex]["command"]

    def get_dev_eui_hex(self, dev_addr_hex):
        dev_eui_hex = None
        for session in self._active_sessions.values():
            if dev_addr_hex == utils.bytes_to_text(session.dev_addr):
                dev_eui_hex = utils.bytes_to_text(session.dev_eui)
                break
        return dev_eui_hex

    def get_nwk_s_key(self, dev_addr_hex):
        dev_eui_hex = self.get_dev_eui_hex(dev_addr_hex=dev_addr_hex)
        if dev_eui_hex in self._active_sessions:
            return self._active_sessions[dev_eui_hex].nwk_s_key

    def get_app_s_key(self, dev_addr_hex):
        dev_eui_hex = self.get_dev_eui_hex(dev_addr_hex=dev_addr_hex)
        if dev_eui_hex in self._active_sessions:
            return self._active_sessions[dev_eui_hex].app_s_key

    def otta_join(self, deveui_hex, devnonce, dlsettings, rxdelay, cflist):
        deveui = bytes.fromhex(deveui_hex)
        appkey = bytes.fromhex(self._devices[deveui_hex]["appkey"])
        logger.info(f"Activating device: {deveui_hex}")
        if not self.has_active_session(dev_eui_hex=deveui_hex):
            self._active_sessions[deveui_hex] = DeviceSession(dev_eui=deveui,
                                                              appkey=appkey)
        joinaccept_phypayload = self._active_sessions[deveui_hex].accept_join(
            devnonce=devnonce, dlsettings=dlsettings, rxdelay=rxdelay, cflist=cflist)
        return joinaccept_phypayload

    def prepare_lorawan_data(self, dev_eui_hex, frmpayload):
        return self._active_sessions[dev_eui_hex].prepare_lorawan_data(frmpayload=frmpayload)
