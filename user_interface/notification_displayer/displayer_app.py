import json
import logging

import gevent.monkey

gevent.monkey.patch_all()

from flask_socketio import SocketIO
import flask
from threading import Thread, Event

import user_interface.notification_displayer.app.forms
import message_queueing
import parameters.message_broker
import user_interface.ui_reports

from logger_configurator import LoggerConfigurator

LoggerConfigurator(level="INFO")
logger = logging.getLogger(__name__)

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# turn the flask app into a socketio app
socketio = SocketIO(app)

# random number Generator Thread
thread = Thread()
thread_stop_event = Event()

refresh_count = 0
config_received = 0

command_sender = message_queueing.MqInterface()


class UiListener(Thread):
    def __init__(self):
        self.mq_interface = message_queueing.MqInterface()
        logger.info("Declaring queue.")
        self.mq_interface.declare_and_consume(queue_name="notifier_display_gui",
                                              routing_key=parameters.message_broker.routing_keys.ui_all_users + '.display',
                                              callback=self.process_received_display_msg,
                                              durable=False,
                                              exclusive=False,
                                              auto_delete=True)
        self.mq_interface.declare_and_consume(queue_name="notifier_configuration_request",
                                              routing_key=parameters.message_broker.routing_keys.configuration_request,
                                              callback=self.process_configuration_request_msg,
                                              durable=False,
                                              exclusive=False,
                                              auto_delete=True)
        self.mq_interface.declare_and_consume(queue_name="notifier_request_action_gui",
                                              routing_key=parameters.message_broker.routing_keys.ui_all_users + '.request',
                                              callback=self.process_gui_action_request_msg,
                                              durable=False,
                                              exclusive=False,
                                              auto_delete=True)
        super(UiListener, self).__init__()

    def process_received_display_msg(self, ch, method, properties, body):
        logger.info(f"Received message to display: {body}")
        message_html_str = user_interface.ui_reports.InputFormBody.build_from_json(body).to_html()
        socketio.emit('display_gui', message_html_str, namespace='/test')

    def process_configuration_request_msg(self, ch, method, properties, body):
        global config_received
        logger.info(f"Received configuration request: {body}")
        config_received += 1
        socketio.emit('ask_config', "<p> Send configuration to TAS!!</p>", namespace='/test')

    def process_gui_action_request_msg(self, ch, method, properties, body):
        logger.info(f"Received configuration request: {body}")
        input_form = user_interface.ui_reports.InputFormBody.build_from_json(body)

        # Check if device configuration is requested:
        if {"DevAddr", "DevEUI", "AppKey"}.issubset({field['name'] for field in input_form.fields}):
            logger.info(f"Dev configuration request received: {body}")
            socketio.emit('user_alerts', "<p>Enter DUT ABP Credentials</p>", namespace='/test')
            socketio.emit('ask_dut', "Enable DUT button", namespace='/test')
        elif {"START"} == {field['name'] for field in input_form.fields}:
            logger.info(f"Start button received: {body}")
            socketio.emit('user_alerts', "<p>Press start after the Agent is running.</p>",
                          namespace='/test')
        else:
            logger.info(f"UI input requested: {body}")
            socketio.emit('user_alerts', input_form.to_html(), namespace='/test')

    def run(self):
        logger.info("Starting consume.")
        self.mq_interface.consume_start()


@app.route('/')
def index():
    global refresh_count
    flask.flash(f"Reload count = {refresh_count}")
    refresh_count += 1

    # only by sending this page first will the client be connected to the socketio instance
    logger.info("Rendering index.html.")
    return flask.render_template('index.html')


@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    logger.info('Client connected')

    # Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        logger.info("Starting Thread")
        thread = UiListener()
        thread.start()

    socketio.emit('user_alerts', "Ready to start: make launch_test_session",
                  namespace='/test')


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    logger.info('Client disconnected')


@socketio.on('send_config', namespace='/test')
def send_config(config):
    logger.info(f"Received config {config} {type(config)}.")
    command_sender.publish(
        exchange_name='amq.topic',
        routing_key=parameters.message_broker.routing_keys.command_configuration_reply,
        msg=json.dumps({"api_version": "1.0.1",
                        "testcases": config}))


@socketio.on('personalize_dut', namespace='/test')
def personalize_dut(config):
    logger.info(f"Received config {config} {type(config)}.")
    dut_info_dict = json.loads(config)
    device_info = {
        'fields': [{"DevAddr": dut_info_dict["devaddr"]},
                   {"AppKey": dut_info_dict["appkey"]},
                   {"DevEUI": dut_info_dict["deveui"]}]}

    command_sender.publish(
        exchange_name='amq.topic',
        routing_key=parameters.message_broker.routing_keys.command_ui_reply,
        msg=json.dumps(device_info))


@socketio.on('start_test', namespace='/test')
def send_config(value):
    logger.info(f"Starting test {value}")
    command_sender.publish(
        exchange_name='amq.topic',
        routing_key=parameters.message_broker.routing_keys.command_ui_reply,
        msg="START SIGNAL")


def main():
    command_sender.declare_queue(queue_name="notifier_display_gui",
                                 durable=False,
                                 exclusive=False,
                                 auto_delete=True)
    command_sender.bind_queue(
        queue_name="notifier_display_gui",
        routing_key=parameters.message_broker.routing_keys.ui_all_users + '.display', )
    command_sender.declare_queue(queue_name="notifier_configuration_request",
                                 durable=False,
                                 exclusive=False,
                                 auto_delete=True)
    command_sender.bind_queue(
        queue_name="notifier_configuration_request",
        routing_key=parameters.message_broker.routing_keys.configuration_request)
    command_sender.declare_queue(queue_name="notifier_request_action_gui",
                                 durable=False,
                                 exclusive=False,
                                 auto_delete=True)
    command_sender.bind_queue(
        queue_name="notifier_request_action_gui",
        routing_key=parameters.message_broker.routing_keys.ui_all_users + '.request')
    logger.info(f"Starting Displayer APP.")
    socketio.run(app, host="0.0.0.0", port=5000)


if __name__ == '__main__':
    main()
