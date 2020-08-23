"""
User side simulator auxiliary module: CLI commands to be used on the User Side
to simulate the messages from a Device Under Test.
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
import os
import re
import click
import json
import pika
import pika.exceptions
import base64
import copy
import lorawan.lorawan_parameters.general
import message_queueing
import parameters.message_broker as broker_parameters

default_ulr = os.environ.get('AMQP_URL')
connection_params = pika.URLParameters(default_ulr)
try:
    connection = pika.BlockingConnection(connection_params)
except pika.exceptions.ConnectionClosed as conn_closed:
    connection = None

empty_mock_msg = {
    'use_dr': 0,
    'freq': 868.5,
    'frmpayload': '',
    'port': 1,
    'fopts': '',
    'confirmed': False,
}


def get_channel(rmq_url=None):
    global connection
    global connection_params
    global default_ulr
    if rmq_url:
        params = pika.URLParameters(rmq_url)
        connection = pika.BlockingConnection(params)
    try:
        channel = connection.channel()
    except pika.exceptions.ConnectionClosed:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
    return channel


def validate_frmpayload(ctx, param, frmpayload_str):
    try:
        frmpayload_bytes = bytes.fromhex(frmpayload_str)
        return frmpayload_bytes
    except ValueError:
        raise click.BadParameter('Bad Frame Payload (e.g. 04ff0201).')


def validate_fopts(ctx, param, fopts):
    try:
        fopts_bytes = bytes.fromhex(fopts)
        return fopts_bytes
    except ValueError:
        raise click.BadParameter('Bad Frame Options field (e.g. 02).')


def validate_tas_api_version(ctx, param, api_version):
    try:
        if not all(v.isdigit() for v in api_version.split(".")):
            raise click.BadParameter('Invalid API version specification.')
        return api_version
    except Exception:
        raise click.BadParameter('Invalid API version specification.')


def validate_testcases(ctx, param, testcases):
    try:
        if not all(
                re.match("td_lorawan_[a-z]{1,4}_[0-9]{1,3}$", tc) for tc in testcases.split(",")):
            raise click.BadParameter('Invalid test list.')
        return testcases
    except Exception:
        raise click.BadParameter('Invalid test list.')


def validate_session_data(field_length, field_str):
    try:
        field_bytes = bytes.fromhex(field_str)
        if len(field_bytes) == field_length:
            return field_bytes
        else:
            raise click.BadParameter(
                'Bad field length: expecting {0} bytes, but got {1}.'.format(field_length,
                                                                             len(field_bytes)))
    except ValueError:
        raise click.BadParameter('Bad field format. (e.g. {}).'.format("01" * field_length))


def validate_eui(ctx, param, eui_str):
    return validate_session_data(field_length=8, field_str=eui_str)


def validate_key(ctx, param, key_str):
    return validate_session_data(field_length=16, field_str=key_str)


def validate_devaddr(ctx, param, devaddr_str):
    return validate_session_data(field_length=4, field_str=devaddr_str)


@click.command()
@click.option('--frmpayload', callback=validate_frmpayload, default="ffffffffff", type=str,
              help='bytes to be sent (e.g. 01af02). Default: ffffffffff')
@click.option('--fopts', callback=validate_fopts, default="", type=str,
              help='Bytes of the FOpts fiedl of the FHDR (e.g. 02). Empty by default')
@click.option('--fport', default=2, type=click.IntRange(0, 255, clamp=False),
              help="Integer value of the desired port (e.g. 224). Default value: 2")
@click.option('--use_confirmed',
              default=False,
              is_flag=True,
              help='Flag that indicates to use a confirmed message. Default: False (Unconfirmed)')
def send(frmpayload, fopts, fport, use_confirmed):
    """Command used to send data or MAC commands in the frmpayload of a lorawan message."""
    global empty_mock_msg
    click.echo("FRMPayload: {0}".format(frmpayload))
    click.echo("FPort: {0}".format(fport))
    click.echo("FOpts: {0}".format(fopts))
    click.echo("Use confirmed: {0}".format(use_confirmed))
    mockmsg = copy.copy(empty_mock_msg)
    mockmsg["frmpayload"] = base64.b64encode(frmpayload).decode()
    mockmsg["fopts"] = base64.b64encode(fopts).decode()
    mockmsg["port"] = fport
    if use_confirmed:
        mockmsg["confirmed"] = True
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.up.data',
                                body=json.dumps(mockmsg))


# noinspection PyProtectedMember
def validate_use_dr(ctx, param, use_dr):
    if use_dr not in lorawan.lorawan_parameters.general.LORA_DR._asdict().keys():
        raise click.BadParameter("Invalid LoRa Data Rate (DR).")
    return use_dr


def validate_freq(ctx, param, freq):
    if freq not in lorawan.lorawan_parameters.general.MIN_LORA_FREQ:
        raise click.BadParameter("Invalid LoRa frequency for this Region.")
    return freq


@click.command()
@click.option('--freq', callback=validate_freq, default=868.1, type=float,
              help="Adds this frequency to be used (e.g. 868.3). Default: 868.1.")
@click.option('--use_dr', callback=validate_use_dr, default='DR0', type=str,
              help="Set the data rate (e.g. DR2). Default: DR0.")
@click.option('--reset_abp_keys',
              default=False,
              is_flag=True,
              help='Reset the keys and device address to the ABP values.')
def configure_device_mock(freq, use_dr, reset_abp_keys):
    """Use this command to configure the lorawan_parameters of the end device mock."""
    click.echo("Configuring")
    click.echo("freq: {0}".format(freq))
    click.echo("Data Rate: {0}".format(use_dr))
    mockmsg = copy.copy(empty_mock_msg)
    mockmsg["use_dr"] = use_dr
    mockmsg["freq"] = freq
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.configure',
                                body=json.dumps(mockmsg))
    if reset_abp_keys:
        get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                    routing_key='mock.configure.resetABP',
                                    body="")


@click.command()
def show_info():
    """ Use this command to print the end device mock information in the agent."""
    click.echo("Requesting mock device session information.")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.configure.showinfo',
                                body="")


@click.command()
def send_actok():
    """ Sends an Activation OK message to the testing tool."""
    click.echo("Sending ACT OK")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.up.message.actok',
                                body="")


@click.command()
def send_join():
    """Sends a join request message to the testing tool."""
    click.echo("Sending Join Accept")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.up.message.join',
                                body="")


@click.command()
def send_pong():
    """Sends a the PONG response of the last received PING to the testing app."""
    click.echo("Sending PONG")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.up.message.pong',
                                body="")


@click.command()
@click.option('--api_version', callback=validate_tas_api_version, default="1.0.1", type=str,
              help="Specify the TAS API version in the configuration.")
@click.option('--testcases', callback=validate_testcases, default="td_lorawan_act_02", type=str,
              help="Specify the list of test cases to run in the TAS session.")
def send_tas_config(api_version, testcases):
    """Send the TAS configuration with indicating the API version and the testcases."""
    click.echo(
        "Sending TAS configuration, testcases: {}({}), api_version: {}({})".format(
            testcases,
            type(testcases),
            api_version,
            type(api_version)))
    get_channel().basic_publish(
        exchange='amq.topic',
        routing_key=broker_parameters.routing_keys.command_configuration_reply,
        body=json.dumps({"api_version": api_version,
                         "testcases": testcases.split(",")}))


@click.command()
@click.option('--deveui', callback=validate_eui, default="0101010101010101", type=str,
              help='ABP: DevEUI (e.g. 0101010101010101). Default: 0101010101010101')
@click.option('--devaddr', callback=validate_devaddr, default="01010101", type=str,
              help='ABP: DevAddr (e.g. 01010101). Default: 01010101')
@click.option('--appkey', callback=validate_key, default="2b7e151628aed2a6abf7158809cf4f3c",
              type=str,
              help='ABP: AppKey (e.g. 2b7e151628aed2a6abf7158809cf4f3c, default value).')
def send_deviceid_to_tas(deveui, devaddr, appkey):
    device_info = {
        'fields': [{"DevAddr": devaddr.hex()}, {"AppKey": appkey.hex()}, {"DevEUI": deveui.hex()}]}

    click.echo(
        "Sending TAS the Device information: {}".format(device_info))
    get_channel().basic_publish(
        exchange='amq.topic',
        routing_key=broker_parameters.routing_keys.command_ui_reply,
        body=json.dumps(device_info))


@click.command()
def send_start_signal():
    click.echo("Starting TAS")
    get_channel().basic_publish(
        exchange='amq.topic',
        routing_key=broker_parameters.routing_keys.command_ui_reply,
        body="START_SIGNAL")
