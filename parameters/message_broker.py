"""
Message broker parameters and used routing keys.
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


RoutingKeys = collections.namedtuple("RoutingKeys", '''
                                     fromAgent,
                                     up_tas,
                                     toAgent,
                                     config_tas,
                                     testing_ready,
                                     testing_configured,
                                     testing_start,
                                     testing_terminate,
                                     session_configuration,
                                     ui_all_users,
                                     configuration_request,
                                     configuration_reply,
                                     command_configuration_reply,
                                     command_ui_reply'''
                                     )


routing_keys = RoutingKeys(
    fromAgent="fromAgent",
    up_tas="up.tas",
    toAgent="toAgent",
    config_tas="config.tas",
    testing_ready="testingtool.ready",
    testing_configured="testingtool.configured",
    testing_start="testsuite.start",
    testing_terminate="testingtool.terminate",
    session_configuration="session.configuration",
    ui_all_users="ui.user.all",
    configuration_request="ui.core.session.configuration.get.request",
    configuration_reply="ui.core.session.configuration.get.reply",
    command_configuration_reply="comm.config.reply",
    command_ui_reply="comm.ui.reply"
)


ServiceNamePrefix = collections.namedtuple("ServiceNamePrefix", '''testingtool,
                                                                   test_session_coordinator,
                                                                   payload_forwarder''')


service_names = ServiceNamePrefix(
    testingtool="testingtool",
    test_session_coordinator="tsc",
    payload_forwarder="pfw"
)

