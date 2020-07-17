"""
Testing Application Protocol parameters.
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
import collections

TESTING_PORT = 224

TestCode = collections.namedtuple("TestCode", "ACTIVATE PINGPONG USE_CONFIRMED USE_UNCONFIRMED \
                                                TRIGGER_JOIN DEACTIVATE LINKCHECK")

TEST_CODE = TestCode(
    DEACTIVATE=b'\x00',
    ACTIVATE=b'\x01',
    USE_CONFIRMED=b'\x02',
    USE_UNCONFIRMED=b'\x03',
    PINGPONG=b'\x04',
    LINKCHECK=b'\x05',
    TRIGGER_JOIN=b'\x06',
)

FrmPayload = collections.namedtuple("FrmPayload", "TEST_DEACTIVATE TEST_ACT")
FRMPAYLOAD = FrmPayload(
    TEST_DEACTIVATE=b'\x00',
    TEST_ACT=b'\x01\x01\x01\x01',
)

