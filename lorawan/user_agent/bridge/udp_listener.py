"""
Module providing the functionality of concurrently listening for UDP messages.
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
import threading


class UDPListener(threading.Thread):
    """
    The UDP listener is in charge of concurrently running the uplink message handler while
    the main task continues its execution.
    """
    def __init__(self, ctx_mqinterface):
        """
        (UDPListener, MqInterface) -> (None)

        :param ctx_mqinterface: reference to the MqInterface that contains this UDP listener.
        """
        threading.Thread.__init__(self)
        self.ctx_interface = ctx_mqinterface
        self.ctx_interface.downlink_ready_semaphore.acquire()

    def run(self):
        """ Starts listening to uplink messages."""
        while True:
            self.ctx_interface.process_uplink_data()

    @classmethod
    def create_semaphore(cls):
        """ Auxiliary method to create semaphores."""
        return threading.Semaphore()

    @classmethod
    def create_lock(cls):
        """ Auxiliary method to create Locks"""
        return threading.RLock()

