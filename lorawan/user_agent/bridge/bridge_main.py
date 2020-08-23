"""
Main module containing the main entry point of the Agent Bridge.
"""
#################################################################################
# MIT License
#
# Copyright (c) 2018, Pablo D. Modernell, Universitat Oberta de Catalunya (UOC),
# Universidad de la Republica Oriental del Uruguay (UdelaR).
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
import logging
import click

from lorawan.user_agent.bridge.agent_bridge import SPFBridge
from logger_configurator import LoggerConfigurator

LoggerConfigurator(level="INFO")
logger = logging.getLogger(__name__)


@click.command()
def agent_main():
    """ Agent Bridge service entry point."""
    spf_bridge = SPFBridge()
    logger.info("Starting agent...")
    spf_bridge.listen_spf()
    spf_bridge.downlink_ready_semaphore.acquire()
    logger.info("Ready to forward.")
    spf_bridge.start_listening_downlink()


if __name__ == '__main__':
    agent_main()
