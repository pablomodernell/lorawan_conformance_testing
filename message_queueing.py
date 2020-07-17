"""
This module manages the interaction with the message queueing broker.
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
import os
import pika
import pika.exceptions


mq_broker_url = os.environ.get('AMQP_URL')
params = pika.URLParameters(mq_broker_url)
try:
    mq_connection = pika.BlockingConnection(params)
except pika.exceptions.ConnectionClosed as conn_closed:
    mq_connection = None

DEFAULT_EXCHANGE = 'amq.topic'


class MqInterface(object):
    """ Wrapper class for interfacing with the message broker."""

    def __init__(self):
        """
        The lorawan_parameters for the connection with the RMQ Broker must be in an
        environment variable *AMQP_URL*.
        """
        global mq_broker_url
        global params
        global mq_connection
        self.amqp_url = mq_broker_url
        if mq_connection and mq_connection.is_open:
            self._connection = mq_connection
        else:
            self._connection = pika.BlockingConnection(params)
        self._channel = self.connection.channel()
        self._knownQueues = []
        self._knownExchanges = []

    @property
    def connection(self):
        global mq_connection
        if mq_connection and mq_connection.is_open:
            self._connection = mq_connection
        else:
            mq_connection = pika.BlockingConnection(params)
            self._connection = mq_connection
        return self._connection

    @property
    def channel(self):
        if self._channel.is_closed:
            self._channel = self.connection.channel()
        return self._channel

    def declare_queue(self, queue_name, exclusive=True, auto_delete=False):
        """
        Declares a new queue in the message broker.
        :param queue_name:
        :param exclusive:
        :param auto_delete:
        :return: queue result
        """
        queue_result = self.channel.queue_declare(queue=queue_name, exclusive=exclusive, auto_delete=auto_delete)
        if queue_name not in self._knownQueues:
            self._knownQueues.append(queue_name)
        return queue_result

    def bind_queue(self, queue_name, routing_key, exchange_name=DEFAULT_EXCHANGE):
        self.channel.queue_bind(queue=queue_name,
                                exchange=exchange_name,
                                routing_key=routing_key)

    def create_consumer(self, callback, queue_name, tag="", auto_ack=True):
        return self.channel.basic_consume(consumer_callback=callback,
                                          queue=queue_name,
                                          no_ack=auto_ack,
                                          consumer_tag=tag)

    def declare_and_consume(self, queue_name, routing_key, callback, exclusive=True, auto_delete=False, auto_ack=True):
        queue_result = self.declare_queue(queue_name, exclusive=exclusive, auto_delete=auto_delete)
        self.bind_queue(exchange_name=DEFAULT_EXCHANGE,
                        queue_name=queue_name,
                        routing_key=routing_key)
        consumer_tag = self.create_consumer(callback=callback,
                                            queue_name=queue_name,
                                            auto_ack=auto_ack)
        return queue_result, consumer_tag

    def publish(self, msg, routing_key, exchange_name=DEFAULT_EXCHANGE):
        self.channel.basic_publish(exchange=exchange_name,
                                   routing_key=routing_key,
                                   body=msg)

    def consume_start(self):
        """
        Start consuming messages.
        :return:
        """
        self.channel.start_consuming()

    def consume_stop(self):
        """
        Cancels all consumers.
        :return:
        """
        self.channel.stop_consuming()


