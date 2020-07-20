import logging
import struct
import random
import utils
import downlink_scheduler_tool.scheduler_errors as scheduler_errors
import downlink_scheduler_tool.devices_data as dev_data
import lorawan.lorawan_parameters.general as lorawan_parameters

import sqlalchemy as sqla
from sqlalchemy.ext.declarative import declarative_base
from postgresclient import db_utils

Base = declarative_base()

logger = logging.getLogger(__name__)


class DeviceSession(Base):
    __tablename__ = "device_session_config"

    dev_eui_hex = sqla.Column(sqla.String, nullable=False, index=True, primary_key=True)
    appkey_hex = sqla.Column(sqla.String, nullable=False)
    dev_addr_hex = sqla.Column(sqla.String, nullable=True)
    nwk_s_key_hex = sqla.Column(sqla.String, nullable=True)
    app_s_key_hex = sqla.Column(sqla.String, nullable=True)
    last_join_accept_hex = sqla.Column(sqla.String, nullable=True)
    used_otaa_devnonces_hex = sqla.Column(sqla.String, nullable=True)
    fcnt_down = sqla.Column(sqla.Integer, nullable=False)

    def __init__(self, dev_eui_hex, appkey_hex, dev_addr_hex=None, app_s_key_hex=None,
                 nwk_s_key_hex=None, fcnt_down=0):
        self.dev_eui_hex = dev_eui_hex
        self.appkey_hex = appkey_hex
        self.dev_addr_hex = dev_addr_hex
        self.app_s_key_hex = app_s_key_hex
        self.nwk_s_key_hex = nwk_s_key_hex
        self.fcnt_down = fcnt_down
        self.last_join_accept_hex = None
        self.used_otaa_devnonces_hex = ""

        self._used_otaa_appnonces = []

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
        return random.randint(0, 2 ** 24 - 1)

    def get_used_devnoce_hex_list(self):
        if self.used_otaa_devnonces_hex is None:
            return []
        else:
            return self.used_otaa_devnonces_hex.split(",")

    def get_last_devnonce_hex(self):
        return self.get_used_devnoce_hex_list()[-1]

    def store_used_devnonce(self, devnonce_bytes):
        """
        (EndDevice, int) -> (None)
        Store the used device nonce to avoid repeated use of the same value and prevent replay attacks.
        :param devnonce: (int) Value to store as a used device nonce.
        :return: None
        """
        devnonce_hex_new = utils.bytes_to_text(devnonce_bytes)
        devnonce_hex_list = self.get_used_devnoce_hex_list()
        if devnonce_hex_new in devnonce_hex_list:
            raise scheduler_errors.DuplicatedNonce()
        if len(devnonce_hex_list) > 3:
            devnonce_hex_list = devnonce_hex_list[1:]
        devnonce_hex_list.append(devnonce_hex_new)
        self.used_otaa_devnonces_hex = ",".join(devnonce_hex_list)

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

        appkey_bytes = bytes.fromhex(self.appkey_hex)
        nwkskey = utils.aes128_encrypt(appkey_bytes, b'\x01' + appnonce_netid_devnonce + bytes(7))
        appskey = utils.aes128_encrypt(appkey_bytes, b'\x02' + appnonce_netid_devnonce + bytes(7))
        logger.info(f"AppSKey: {utils.bytes_to_text(appskey)}")
        logger.info(f"NwkSKey: {utils.bytes_to_text(nwkskey)}")
        self.store_used_devnonce(devnonce)
        macpayload = appnonce + netid[::-1] + devaddr[::-1] + dlsettings + rxdelay + cflist
        mhdr_macpayload = lorawan_parameters.MHDR.JOIN_ACCEPT + macpayload
        mic = utils.aes128_cmac(appkey_bytes, mhdr_macpayload)[:4]

        join_accept_phypayload = (lorawan_parameters.MHDR.JOIN_ACCEPT +
                                  utils.aes128_decrypt(key=appkey_bytes,
                                                       cipher_text=macpayload + mic)
                                  )
        devaddr_hex = utils.bytes_to_text(devaddr)
        appskey_hex = utils.bytes_to_text(appskey)
        nwkskey_hex = utils.bytes_to_text(nwkskey)
        self.update_device_session(devaddr_hex=devaddr_hex, appskey_hex=appskey_hex,
                                   nwkskey_hex=nwkskey_hex)

        self.rx1_dr_offset = (int.from_bytes(dlsettings, byteorder='big') & 0x70) >> 4
        rx2_dr = (int.from_bytes(dlsettings, byteorder='big') & 0x0f)
        self.rx2_dr = lorawan_parameters.LORA_DR[rx2_dr]
        seconds_delay = max(1, (int.from_bytes(rxdelay, byteorder='big') & 0x0f))
        self.rx1_delay = seconds_delay * lorawan_parameters.TIMING.MS_IN_SEC

        self.last_join_accept_hex = utils.bytes_to_text(join_accept_phypayload)

    def update_device_session(self, devaddr_hex, appskey_hex, nwkskey_hex):
        self.dev_addr_hex = devaddr_hex
        self.app_s_key_hex = appskey_hex
        self.nwk_s_key_hex = nwkskey_hex

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
        dev_addr_bytes = bytes.fromhex(self.dev_addr_hex)
        fhdr = dev_addr_bytes[::-1] + fctr + struct.pack('<H', fcnt_down) + fopts
        mhdr_fhdr = mhdr + fhdr
        assert mhdr in (
            b'\x00', b'\x40', b'\x80', b'\x20', b'\x60', b'\xA0', b'\xC0'), "Unrecognized MHDR."
        if mhdr in (b'\x00', b'\x40', b'\x80'):
            direction = 0
        else:
            direction = 1
        nwk_s_key_bytes = bytes.fromhex(self.nwk_s_key_hex)
        app_s_key_bytes = bytes.fromhex(self.app_s_key_hex)
        if fport is not None and frmpayload is not None:
            if fport == 0:
                key = nwk_s_key_bytes
            else:
                key = app_s_key_bytes
            mac_hdr_payload = mhdr_fhdr + struct.pack('B', fport) + utils.encrypt_ieee802154(
                key=key,
                frmpayload=frmpayload,
                direction=direction,
                devaddr=dev_addr_bytes,
                fcnt=fcnt_down)
        else:
            mac_hdr_payload = mhdr_fhdr
        phy_payload = mac_hdr_payload + utils.mic_rfc4493(key=nwk_s_key_bytes,
                                                          msg=mac_hdr_payload,
                                                          direction=direction,
                                                          devaddr=dev_addr_bytes,
                                                          fcnt=fcnt_down)
        return phy_payload


class DevicesSessionHandler(object):
    def __init__(self, db_config):
        self._devices = dev_data.devices_to_configure
        self._active_sessions = {}
        database_uri = "postgresql://{}:{}@{}:{}/{}".format(db_config["user"],
                                                            db_config["password"],
                                                            db_config["host"],
                                                            db_config["port"],
                                                            db_config["database"])
        db_utils.create_db(**db_config)
        engine = sqla.create_engine(database_uri)
        engine.connect()
        Session = sqla.orm.sessionmaker(bind=engine)
        self.session = Session()
        Base.metadata.create_all(engine)
        try:
            self.session.execute(sqla.text("""CREATE TABLE alembic_version (
                        version_num character varying(32) NOT NULL,
                        PRIMARY KEY (version_num)
                        );
                """))
            self.session.execute(
                sqla.text("""INSERT INTO alembic_version VALUES ('c4821ceae1a2')"""))
            self.session.commit()
        except:
            logger.warning("Table alembic_version already exist")
            self.session.rollback()

    def query_dev_eui_hex(self, dev_eui_hex):
        return self.session.query(DeviceSession).filter(
            DeviceSession.dev_eui_hex == dev_eui_hex).first()

    def query_dev_addr_hex(self, dev_addr_hex):
        return self.session.query(DeviceSession).filter(
            DeviceSession.dev_addr_hex == dev_addr_hex).first()

    def is_registered(self, dev_eui_hex, app_eui_hex=None):
        if dev_eui_hex not in self._devices:
            return False
        if not app_eui_hex or "appeui" not in self._devices[dev_eui_hex]:
            return True
        return self._devices[dev_eui_hex]["appeui"] == app_eui_hex

    def has_active_session(self, dev_eui_hex):
        dev_session = self.query_dev_eui_hex(dev_eui_hex=dev_eui_hex)
        return dev_session is not None

    def get_appkey_hex(self, dev_eui_hex):
        if self.is_registered(dev_eui_hex=dev_eui_hex):
            return self._devices[dev_eui_hex]["appkey"]

    def get_command_hex(self, dev_addr_hex):
        dev_eui_hex = self.get_dev_eui_hex(dev_addr_hex=dev_addr_hex)
        if self.is_registered(dev_eui_hex=dev_eui_hex):
            return self._devices[dev_eui_hex]["command"]

    def get_dev_eui_hex(self, dev_addr_hex):
        dev_session = self.query_dev_addr_hex(dev_addr_hex=dev_addr_hex)
        dev_eui_hex = None
        if dev_session is not None:
            dev_eui_hex = dev_session.dev_eui_hex
        return dev_eui_hex

    def get_nwk_s_key_hex(self, dev_addr_hex):
        dev_session = self.query_dev_addr_hex(dev_addr_hex=dev_addr_hex)
        nwk_s_key_hex = None
        if dev_session is not None:
            nwk_s_key_hex = dev_session.nwk_s_key_hex
        return nwk_s_key_hex

    def get_app_s_key_hex(self, dev_addr_hex):
        dev_session = self.query_dev_addr_hex(dev_addr_hex=dev_addr_hex)
        app_s_key_hex = None
        if dev_session is not None:
            app_s_key_hex = dev_session.app_s_key_hex
        return app_s_key_hex

    def process_otta_join(self, deveui_hex, devnonce, dlsettings, rxdelay, cflist):
        try:
            appkey_hex = self._devices[deveui_hex]["appkey"]
            dev_session = self.query_dev_eui_hex(dev_eui_hex=deveui_hex)
            if dev_session is None:
                dev_session = DeviceSession(dev_eui_hex=deveui_hex,
                                            appkey_hex=appkey_hex)
                logger.info(
                    f"Creating first session for: {deveui_hex}")
                self.session.add(dev_session)
            dev_session.accept_join(
                devnonce=devnonce, dlsettings=dlsettings, rxdelay=rxdelay, cflist=cflist)
        except Exception as e:
            logger.error(f"Error creating session for device {deveui_hex}.")
        else:
            self.session.commit()

    def get_joinaccept_bytes(self, deveui_hex):
        dev_session = self.query_dev_eui_hex(dev_eui_hex=deveui_hex)
        if dev_session is None:
            logger.error(f"Error getting Join Accept, no session for device {deveui_hex}.")
            return
        join_accept_hex = dev_session.last_join_accept_hex
        if join_accept_hex is None:
            logger.error(f"No Join Accept generated for device {deveui_hex}.")
            return
        return bytes.fromhex(join_accept_hex)

    def prepare_lorawan_data(self, dev_eui_hex, frmpayload):
        dev_session = self.query_dev_eui_hex(dev_eui_hex=dev_eui_hex)
        if dev_session is None:
            logger.error(f"Error Preparing DATA, no session for device {dev_eui_hex}.")
            return
        return dev_session.prepare_lorawan_data(frmpayload=frmpayload)
