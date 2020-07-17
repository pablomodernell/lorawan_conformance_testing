"""
Logger classes of the different testing tool logs. The loggers use standard output to
print the messages with information and also send the logs to the message broker. Any client
interested in seeing the logs could declare a queue and consume with the corresponding routing key.
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
import time

import message_queueing
import parameters.message_broker as msg_broker


class LoggerAll(message_queueing.MqInterface):
    """
    Captures and prints all the logs.
    """

    def __init__(self):
        super().__init__()
        self.declare_and_consume(queue_name="logger_all",
                                 routing_key="log.#",
                                 callback=self.handle_all_logs,
                                 exclusive=False,
                                 auto_delete=True)

    def start_logging(self):
        self.consume_start()

    def handle_all_logs(self, ch, method, properties, body):
        print("{0:10.2f}: {1}".format(time.time(),
                                      body.decode()),
              flush=True)


class PayloadForwarderLog(message_queueing.MqInterface):
    """
    Captures and prints the log messages from the Payload Forwarder.
    """

    def __init__(self):
        super().__init__()
        self.declare_and_consume(queue_name="logger_pfw",
                                 routing_key="log." + msg_broker.service_names.payload_forwarder,
                                 callback=self.handle_nfw_logs,
                                 exclusive=False,
                                 auto_delete=True)

    def start_logging(self):
        self.consume_start()

    def handle_nfw_logs(self, ch, method, properties, body):
        print("{0:10.2f} {1}: {2}".format(time.time(),
                                          msg_broker.service_names.payload_forwarder,
                                          body.decode()),
              flush=True)


class TestServerLog(message_queueing.MqInterface):
    """
    Captures and prints the log messages from the Payload Forwarder.
    """

    def __init__(self):
        super().__init__()
        self.declare_and_consume(queue_name="logger_tas",
                                 routing_key="log." + msg_broker.service_names.test_session_coordinator,
                                 callback=self.handle_tas_logs,
                                 exclusive=False,
                                 auto_delete=True)

    def start_logging(self):
        self.consume_start()

    def handle_tas_logs(self, ch, method, properties, body):
        print("{0:10.2f} {1}: {2}".format(time.time(),
                                          msg_broker.service_names.test_session_coordinator,
                                          body.decode()),
              flush=True)






