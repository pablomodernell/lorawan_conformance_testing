"""
conftest is a “local plugin” that can contain hook functions and fixtures. Hook functions are a way to insert code
into part of the pytest execution process to alter how pytest works. Fixtures are setup and teardown functions that
run before and after test functions, and can be used to represent resources and data used by the tests.
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
import pytest
import base64


# @pytest.fixture(scope=​ 'session'​, params=[​ 'tiny'​, ​ 'mongo'​])
@pytest.fixture(scope='session')  # scope could be function, class, module or session
def default_test_key():
    return b'\x2B\x7E\x15\x16\x28\xAE\xD2\xA6\xAB\xF7\x15\x88\x09\xCF\x4F\x3C'


@pytest.fixture(scope='session')
def device_session_id():
    return {
        "DevAddr": base64.b64decode("ASgpnw=="),
        "DevEUI": base64.b64decode("AASjCwAa2+U="),
        "AppKey": base64.b64decode("K34VFiiu0qar9xWICc9PPA=="),
        "AppSKey": base64.b64decode("K34VFiiu0qar9xWICc9PPA=="),
        "NwkSKey": base64.b64decode("K34VFiiu0qar9xWICc9PPA==")
    }

