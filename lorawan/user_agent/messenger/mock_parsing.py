"""
User side simulator auxiliary module: message parsing for the message simulator.
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

import base64
import json


class MockMessage(object):
    """
    Message containing the information sent by the command line interface to the agent mock in order
    to request data being sent to the server. It is also used to to configure de end device mock (e.g. add frequency,
    set used data rate, change session keys)
    {
        'use_dr': 2,
        'freq': 868.5,
        'frmpayload': 'QJ8pKAGAAAACBq6JhF/uO9ZeeoSq4xZMFchm3lw=',
        'port': 1,
    }
    """

    def __init__(self, json_mockmsg_str):
        """
        (str) -> (MockMessage)
        :param json_mockmsg_str: string-json formatted.
        """
        self.mock_message_dict = json.loads(json_mockmsg_str)

    def __str__(self):
        return json.dumps(self.mock_message_dict)

    @property
    def frmpayload_bytes(self):
        return base64.b64decode(self.mock_message_dict["frmpayload"])

    @property
    def fport(self):
        return self.mock_message_dict["port"]

    @property
    def use_dr(self):
        return self.mock_message_dict["use_dr"]

    @property
    def freq(self):
        return self.mock_message_dict["freq"]

    @property
    def fopts_bytes(self):
        return base64.b64decode(self.mock_message_dict["fopts"])

    @property
    def is_confirmed(self):
        return self.mock_message_dict["confirmed"]
