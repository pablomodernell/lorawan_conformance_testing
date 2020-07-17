import json
import pika
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

LoggerConfigurator(level="DEBUG")
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


class UiListener(Thread):
    def __init__(self):
        self.mq_interface = message_queueing.MqInterface()
        print("Declaring queue.")
        logger.debug("Declaring queue.")
        self.mq_interface.declare_and_consume(queue_name="notifier_display_gui",
                                              routing_key=parameters.message_broker.routing_keys.ui_all_users + '.display',
                                              callback=self.process_received_display_msg,
                                              exclusive=False)
        self.mq_interface.declare_and_consume(queue_name="notifier_configuration_request",
                                              routing_key=parameters.message_broker.routing_keys.configuration_request,
                                              callback=self.process_configuration_request_msg,
                                              exclusive=False)
        self.mq_interface.declare_and_consume(queue_name="notifier_request_action_gui",
                                              routing_key=parameters.message_broker.routing_keys.ui_all_users + '.request',
                                              callback=self.process_gui_action_request_msg,
                                              exclusive=False)
        super(UiListener, self).__init__()

    def process_received_display_msg(self, ch, method, properties, body):
        print(f"Received message to display: {body}")
        logger.debug(f"Received message to display: {body}")
        message_html_str = user_interface.ui_reports.InputFormBody.build_from_json(body).to_html()
        socketio.emit('display_gui', message_html_str, namespace='/test')

    def process_configuration_request_msg(self, ch, method, properties, body):
        global config_received
        print(f"Received configuration request: {body}")
        logger.debug(f"Received configuration request: {body}")
        config_received += 1
        socketio.emit('user_alerts', "<p> Send configuration to TAS!!</p>", namespace='/test')
        # ch.basic_ack(delivery_tag=method.delivery_tag)

    def process_gui_action_request_msg(self, ch, method, properties, body):
        print(f"Received configuration request: {body}")
        logger.debug(f"Received configuration request: {body}")
        input_form = user_interface.ui_reports.InputFormBody.build_from_json(body)

        # Check if device configuration is requested:
        if {"DevAddr", "DevEUI", "AppKey"}.issubset({field['name'] for field in input_form.fields}):
            print(f"Dev configuration request received: {body}")
            logger.debug(f"Dev configuration request received: {body}")
            socketio.emit('user_alerts', "<p>Enter DUT ABP Credentials</p>", namespace='/test')
        elif {"START"} == {field['name'] for field in input_form.fields}:
            print(f"Start button received: {body}")
            logger.debug(f"Start button received: {body}")
            socketio.emit('user_alerts', "<p>Press start after the Agent is running.</p>", namespace='/test')
        else:
            print(f"UI input requested: {body}")
            logger.debug(f"UI input requested: {body}")
            socketio.emit('user_alerts', input_form.to_html(), namespace='/test')

    def run(self):
        print("Starting consume.")
        logger.debug("Starting consume.")
        self.mq_interface.consume_start()


@app.route('/')
def index():
    global refresh_count
    flask.flash(f"Reload count = {refresh_count}")
    refresh_count += 1

    # only by sending this page first will the client be connected to the socketio instance
    logger.debug("Rendering index.html.")
    return flask.render_template('index.html')


@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')
    logger.debug('Client connected')

    # Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        logger.debug("Starting Thread")
        thread = UiListener()
        thread.start()


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
