import pika
import collections
import message_queueing
from parameters.message_broker import routing_keys


class CommandRequest(object):
    def __init__(self, correlation_id, reply_to_key):
        self.correlation_id = correlation_id
        self.reply_to_key = reply_to_key


class RequestProcessor(message_queueing.MqInterface):
    def __init__(self):
        super().__init__()
        self._ui_commands_queue = collections.deque()
        self._configuration_commands_queue = collections.deque()

        self.declare_and_consume(queue_name='comm_configuration_request',
                                 exclusive=False,
                                 routing_key=routing_keys.configuration_request,
                                 durable=False,
                                 auto_delete=True,
                                 callback=self.process_configuration_request)

        self.declare_and_consume(queue_name='comm_ui_request',
                                 exclusive=False,
                                 routing_key=f"{routing_keys.ui_all_users}.request",
                                 durable=False,
                                 auto_delete=True,
                                 callback=self.process_ui_request)

        self.declare_and_consume(queue_name='comm_send_configuration_reply',
                                 exclusive=False,
                                 routing_key=routing_keys.command_configuration_reply,
                                 durable=False,
                                 auto_delete=True,
                                 callback=self.send_configuration_reply)

        self.declare_and_consume(queue_name='comm_send_ui_reply',
                                 exclusive=False,
                                 routing_key=routing_keys.command_ui_reply,
                                 durable=False,
                                 auto_delete=True,
                                 callback=self.send_ui_reply)

    def get_configuration_command(self):
        config_command = None
        if self._configuration_commands_queue:
            config_command = self._configuration_commands_queue.popleft()
        return config_command

    def get_ui_command(self):
        ui_command = None
        if self._ui_commands_queue:
            ui_command = self._ui_commands_queue.popleft()
        return ui_command

    def add_configuration_command(self, correlation_id, reply_to_key):
        self._configuration_commands_queue.append(CommandRequest(correlation_id=correlation_id,
                                                                 reply_to_key=reply_to_key))

    def add_ui_command(self, correlation_id, reply_to_key):
        self._ui_commands_queue.append(CommandRequest(correlation_id=correlation_id,
                                                      reply_to_key=reply_to_key))

    def process_configuration_request(self, ch, method, properties, body):
        print(f"Received configuration request: {body}")
        self.add_configuration_command(correlation_id=properties.correlation_id,
                                       reply_to_key=properties.reply_to)

    def process_ui_request(self, ch, method, properties, body):
        print(f"Received UI request: {body}")
        self.add_ui_command(correlation_id=properties.correlation_id,
                            reply_to_key=properties.reply_to)

    def send_configuration_reply(self, ch, method, properties, body):
        print(f"Received configuration reply from CLI: {body}")
        first_conf_command = self.get_configuration_command()
        if first_conf_command is None:
            return
        ch.basic_publish(exchange='amq.topic',
                         routing_key=first_conf_command.reply_to_key,
                         properties=pika.BasicProperties(
                             correlation_id=first_conf_command.correlation_id),
                         body=body)

    def send_ui_reply(self, ch, method, properties, body):
        print(f"Received UI reply from CLI: {body}")
        first_ui_command = self.get_ui_command()
        if first_ui_command is not None:
            ch.basic_publish(exchange='amq.topic',
                             routing_key=first_ui_command.reply_to_key,
                             properties=pika.BasicProperties(
                                 correlation_id=first_ui_command.correlation_id),
                             body=body)
