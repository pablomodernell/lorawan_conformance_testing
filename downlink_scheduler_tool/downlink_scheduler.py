import utils
import message_queueing
from parameters.message_broker import routing_keys
from lorawan.parsing import flora_messages
import downlink_scheduler_tool.devices_sessions as devices_sessions
import lorawan.lorawan_parameters.general as lorawan_parameters
import downlink_scheduler_tool.scheduler_errors as scheduler_errors

import logging

logger = logging.getLogger(__name__)


class DownlinkScheduler(object):
    def __init__(self,
                 db_config,
                 accept_dlsettings=lorawan_parameters.DLSETTINGS.RX1OFFSET0_RX2DR0,
                 accept_rxdelay=lorawan_parameters.JOIN_ACCEPT_RXDELAY.DELAY0,
                 accept_cflist=lorawan_parameters.JOIN_ACCEPT_CFLIST.NO_CHANNELS):
        self.uplink_mq_interface = message_queueing.MqSelectConnectionInterface(
            queue_name='up_downlink_scheduler',
            queue_durable=False,
            queue_auto_delete=True,
            routing_key=routing_keys.fromAgentToScheduler,
            on_message_callback=self.up_message_handler)
        self.downlink_mq_interface = message_queueing.MqPublisher(
            routing_key=routing_keys.fromAgentToScheduler)

        self.sessions_handler = devices_sessions.DevicesSessionHandler(db_config=db_config)
        self.accept_dlsettings = accept_dlsettings
        self.accept_rxdelay = accept_rxdelay
        self.accept_cflist = accept_cflist

    def start_scheduler(self):
        logger.info("Starting Config Scheduler")
        self.uplink_mq_interface.consume_start()

    def up_message_handler(self, body_str):

        received_testscript_msg = flora_messages.GatewayMessage(
            json_ttm_str=body_str)
        lorawan_msg = received_testscript_msg.parse_lorawan_message()
        logger.info("--------------------------------------------------------\n")
        logger.info(f"Received Uplink: {str(lorawan_msg)}")

        mtype_int = lorawan_msg.mhdr.mtype_int

        if lorawan_msg.mhdr.mhdr_bytes == lorawan_parameters.MHDR.JOIN_REQUEST:
            try:
                devnonce = lorawan_msg.macpayload.devnonce_bytes
                deveui_hex = utils.bytes_to_text(lorawan_msg.macpayload.deveui_bytes).upper()
                appeui_hex = utils.bytes_to_text(lorawan_msg.macpayload.appeui_bytes).upper()
                if not self.sessions_handler.is_registered(dev_eui_hex=deveui_hex,
                                                           app_eui_hex=appeui_hex):
                    logger.info(f"Device Not Registered: {deveui_hex}")
                    return
                self.sessions_handler.process_otta_join(
                    deveui_hex=deveui_hex, devnonce=devnonce,
                    dlsettings=self.accept_dlsettings,
                    rxdelay=self.accept_rxdelay,
                    cflist=self.accept_cflist)
                jaccept_phypayload = self.sessions_handler.get_joinaccept_bytes(
                    deveui_hex=deveui_hex)
                json_nwk_response = received_testscript_msg.create_nwk_response_str(
                    phypayload=jaccept_phypayload,
                    delay=lorawan_parameters.TIMING.JOIN_ACCEPT_DELAY1,
                    datr_offset=lorawan_parameters.DR_OFFSET.RX1_DEFAULT)
                logger.info(f"Sending Join Accept: {str(json_nwk_response)}")

                self.downlink_mq_interface.send(routing_key=routing_keys.fromSchedulerToAgent,
                                                data=json_nwk_response)
            except scheduler_errors.DuplicatedNonce as dne:
                logger.info(f"Ignoring Duplicated nonce {devnonce}")
        elif lorawan_msg.mhdr.mhdr_bytes == lorawan_parameters.MHDR.UNCONFIRMED_UP:
            devaddrhex = utils.bytes_to_text(lorawan_msg.macpayload.fhdr.devaddr_bytes).upper()
            network_key_hex = self.sessions_handler.get_nwk_s_key_hex(dev_addr_hex=devaddrhex)
            if network_key_hex is None:
                logger.info(f"No active session for device: {devaddrhex}")
                return
            network_key = bytes.fromhex(network_key_hex)
            calculated_mic = lorawan_msg.calculate_mic(key=network_key)
            dev_eui_hex = self.sessions_handler.get_dev_eui_hex(dev_addr_hex=devaddrhex)
            if not lorawan_msg.mic_bytes == calculated_mic:
                logger.info(
                    f"Wrong MIC. Expecting {calculated_mic}, Device {dev_eui_hex} ({devaddrhex}).")
            logger.info(f"MIC OK (NwkSKey: {utils.bytes_to_text(network_key)}, dev {dev_eui_hex})")

            frmpayload_command = bytes.fromhex(
                self.sessions_handler.get_command_hex(dev_addr_hex=devaddrhex))
            lw_response = self.sessions_handler.prepare_lorawan_data(dev_eui_hex=dev_eui_hex,
                                                                     frmpayload=frmpayload_command)
            json_nwk_response = received_testscript_msg.create_nwk_response_str(
                phypayload=lw_response,
                delay=lorawan_parameters.TIMING.RECEIVE_DELAY1,
                datr_offset=lorawan_parameters.DR_OFFSET.RX1_DEFAULT)
            logger.info(f"Sending Downlink Data: {str(json_nwk_response)}")
            self.downlink_mq_interface.send(routing_key=routing_keys.fromSchedulerToAgent,
                                            data=json_nwk_response)
