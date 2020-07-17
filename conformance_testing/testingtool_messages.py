"""
Basic structure of the messages exchanged between the different components of the testing tool.
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


class TestingToolMessage(object):
    """
    Base class with the basic structure of a message exchanged between the different services of the testing tool.
    """
    def __init__(self, json_ttm_str):
        """
        Parses a json string to create a message, defines a dictionary with the fields of the message as an attribute.
        (str) -> (TestingToolMessage)
        :param json_ttm_str: string-json formatted.
        """
        self.testingtool_msg_dict = json.loads(json_ttm_str)

    def __str__(self):
        """
        String representation of the testing tool message. This representation could be parsed again to create
        an object of this class.
        :return:
        """
        return json.dumps(self.testingtool_msg_dict, sort_keys=True, indent=4)

    def get_printable_str(self):
        """
        Human readable representation of the testing tool message.
        :return:
        """
        self.__str__()


