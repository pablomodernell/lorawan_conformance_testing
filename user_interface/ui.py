"""
This module provides interaction with the user.
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
import message_queueing
from parameters.message_broker import routing_keys


class UserInterface(message_queueing.MqInterface):
    """ This class handles the interactions with the users, including message publication in the Web UI and logging."""

    def testingtool_log(self, msg_str, key_prefix):
        self.publish(msg=msg_str, routing_key="log."+key_prefix)
        print("{0} Log: {1}".format(key_prefix.upper(), msg_str), flush=True)

    def display_on_gui(self, msg_str, key_prefix="NoLogKey"):
        self.publish(msg=msg_str, routing_key=routing_keys.ui_all_users+'.display')
        self.testingtool_log(msg_str="Display on GUI>> "+msg_str,
                             key_prefix=key_prefix)


ui_publisher = UserInterface()


