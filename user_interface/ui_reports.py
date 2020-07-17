"""
This module defines the format of the different message interaction with the user
interface.
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
import json
from uuid import uuid4
import pika
import abc
import time

from user_interface import API_VERSION
from message_queueing import DEFAULT_EXCHANGE
import user_interface.ui_errors

LEVEL_ERR = "error"
LEVEL_HL = "highlighted"
LEVEL_INFO = "info"


class MessageProperties(object):
    def __init__(self,
                 content_type="application/json",
                 message_id="",
                 timestamp=int(time.time()),
                 reply_to="",
                 correlation_id=str(uuid4())):
        self.content_type = content_type
        self.message_id = message_id
        self.timestamp = timestamp
        self.reply_to = reply_to
        self.correlation_id = correlation_id

    def to_dict(self):
        return {
            "content_type": self.content_type,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "reply_to": self.reply_to,
            "correlation_id": self.correlation_id
        }

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4, sort_keys=True)


class SessionConfigurationBody(object):
    def __init__(self,
                 api_version=API_VERSION,
                 message_id="",
                 testcases=None,
                 session_id="",
                 testing_tools="f-interop/flora",
                 users=None):

        self._api_version = api_version
        if not testcases:
            self.testcases = []
        else:
            self.testcases = testcases

    @classmethod
    def build_from_json(cls, json_str):
        session_configuration_dict = json.loads(json_str)
        if set(session_configuration_dict.keys()).issubset({'api_version', 'message_id',
                                                            'testcases', 'session_id',
                                                            'testing_tools', 'users'}):
            return cls(**session_configuration_dict)
        else:
            raise user_interface.ui_errors.SessionConfigurationBodyError(
                "Error in the provided parameters of SessionConfigurationBody: {json_str}")

    def to_dict(self):
        return {
            "_api_version": self._api_version,
            "testcases": self.testcases
        }

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4, sort_keys=True)


class InputField(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, name="default name", label="default label", value="default value"):
        self.name = name
        self.label = label
        self.value = value
        self.type = None

    @classmethod
    def build_from_json(cls, json_input_field):
        input_field_dict = json.loads(json_input_field)
        field_type = input_field_dict.get('type')
        if set(input_field_dict.keys()).issubset({'name', 'label', 'value', 'type'}) and \
                field_type is not None:
            if field_type == 'p':
                return ParagraphField(name=input_field_dict['name'],
                                      label=input_field_dict['label'],
                                      value=input_field_dict['value'])
            elif field_type == 'text':
                return TextInputField(name=input_field_dict['name'],
                                      label=input_field_dict['label'],
                                      value=input_field_dict['value'])
            elif field_type == 'button':
                return ButtonInputField(name=input_field_dict['name'],
                                        label=input_field_dict['label'],
                                        value=input_field_dict['value'])
            else:
                raise user_interface.ui_errors.UnsupportedFieldTypeError(
                    "Error in the provided parameters of InputField: {json_str}")
        else:
            raise user_interface.ui_errors.InputFieldError(
                "Error in the provided parameters of InputField: {json_str}")

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "label": self.label,
            "value": self.value
        }

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4, sort_keys=True)

    def to_html(self):
        if self.label == 'default label':
            html_str = ''
        else:
            html_str = f'<label for="{self.name}">{self.label}</label>'

        html_str += f'<input id="{self.name}" type="{self.type}" name="{self.name}" value="{self.value}">'
        return html_str


class ParagraphField(InputField):
    def __init__(self, name="default name", label="default label", value="sthg2show"):
        super().__init__(name=name, label=label, value=value)
        self.type = "p"

    def add_line(self, new_line):
        self.value += "\n" + new_line

    def to_html(self):
        if self.label == 'default label':
            html_str = ''
        else:
            html_str = f'<label for="{self.name}">{self.label}</label>'

        html_str += f'<p id="{self.name}" type="{self.type}" name="{self.name}">{self.name}\n{self.value}</p>'

        return html_str


class TextInputField(InputField):
    def __init__(self, name="default name", label="default label", value="default value"):
        super().__init__(name=name, label=label, value=value)
        self.type = "text"


class ButtonInputField(InputField):
    def __init__(self, name="default name", label="default label", value="default value"):
        super().__init__(name=name, label=label, value=value)
        self.type = "button"


class InputFormBody(object, metaclass=abc.ABCMeta):
    def __init__(self, title="Input Title", level=LEVEL_INFO, tag_key=None, tag_value=None):
        self.title = title
        self.level = level
        self.fields = []
        if tag_key and tag_value:
            self.tags = {tag_key: tag_value}
        else:
            self.tags = {"": ""}

    @classmethod
    def build_from_json(cls, json_str):
        input_form_body_dict = json.loads(json_str)
        if set(input_form_body_dict.keys()).issubset({'title', 'level', 'fields',
                                                      'tags'}):
            tag_key = list(input_form_body_dict['tags'])[0]
            tag_value = input_form_body_dict['tags'][tag_key]
            form_body = cls(title=input_form_body_dict['title'],
                            level=input_form_body_dict['level'],
                            tag_key=tag_key,
                            tag_value=tag_value)
            for field in input_form_body_dict['fields']:
                form_body.add_field(InputField.build_from_json(json.dumps(field)))
            return form_body
        else:
            raise user_interface.ui_errors.InputFormBody(
                "Error in the provided parameters of InputFormBody: {json_str}")

    def to_dict(self):
        ret_dict = {
            "title": self.title,
            "level": self.level,
            "fields": self.fields,
            "tags": self.tags
        }
        return ret_dict

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4, sort_keys=True)

    def add_field(self, new_field):
        self.fields.append(new_field.to_dict())

    def get_parsed_reply(self, reply_body):
        """ Returns a dict with the response values {name:value}."""
        reply = json.loads(reply_body.decode())
        parsed_reply = dict()
        for field in self.fields:
            for reply_field in reply["fields"]:
                if field["name"] in reply_field:
                    parsed_reply[field["name"]] = reply_field[field["name"]]
                    break

        return parsed_reply

    def to_html(self):
        tag_to_id = ""
        if self.tags:
            tag_key = list(self.tags)[0]
            tag_to_id = f'id="{tag_key}_{self.tags[tag_key]}"'
        html_str = f'<div {tag_to_id}><p>{self.title}</p>'
        for field in self.fields:
            html_str += InputField.build_from_json(json.dumps(field)).to_html()
        html_str += '</div>'
        return html_str


class RPCRequest(object):
    def __init__(self, request_key, channel, body):
        self.channel = channel
        self.connection = channel.connection
        self.request_key = request_key
        self.body = body
        self.reply_to = request_key.replace("request", "reply")
        self.correlation_id = None
        self.response_body = None
        self.consumer_tag = None
        self.temporary_queue = None

    def on_response(self, ch, method, properties, body):
        if self.correlation_id == properties.correlation_id:
            self.response_body = body
            ch.basic_ack(delivery_tag=method.delivery_tag)
            ch.stop_consuming(consumer_tag=self.consumer_tag)

    def wait_response(self, timeout_seconds=None):
        # TODO: handle timeout
        queue_result = self.channel.queue_declare(exclusive=True)
        self.temporary_queue = queue_result.method.queue
        self.channel.queue_bind(queue=self.temporary_queue,
                                exchange=DEFAULT_EXCHANGE,
                                routing_key=self.reply_to)
        self.consumer_tag = self.channel.basic_consume(consumer_callback=self.on_response,
                                                       no_ack=False,
                                                       queue=self.temporary_queue)
        self.correlation_id = str(uuid4())
        time.sleep(1)
        self.channel.basic_publish(exchange=DEFAULT_EXCHANGE,
                                   routing_key=self.request_key,
                                   properties=pika.BasicProperties(reply_to=self.reply_to,
                                                                   correlation_id=self.correlation_id),
                                   body=self.body)

        while self.response_body is None:
            self.connection.process_data_events()
            time.sleep(0.1)
        return self.response_body
