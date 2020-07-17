"""
User side simulator auxiliary module: message simulator handler.
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
import click

import lorawan.user_agent.messenger.generator as gen
from lorawan.parsing.configuration import DeviceID


def validate_session_data(field_length, field_str):
    try:
        field_bytes = bytes.fromhex(field_str)
        if len(field_bytes) == field_length:
            return field_bytes
        else:
            raise click.BadParameter('Bad field length: expecting {0} bytes, but got {1}.'.format(field_length,
                                                                                                  len(field_bytes)))
    except ValueError:
        raise click.BadParameter('Bad field format. (e.g. {}).'.format("01"*field_length))


def validate_eui(ctx, param, eui_str):
    return validate_session_data(field_length=8, field_str=eui_str)


def validate_key(ctx, param, key_str):
    return validate_session_data(field_length=16, field_str=key_str)


def validate_devaddr(ctx, param, devaddr_str):
    return validate_session_data(field_length=4, field_str=devaddr_str)


@click.command()
@click.option('--deveui', callback=validate_eui, default="0101010101010101", type=str,
              help='ABP: DevEUI (e.g. 0101010101010101). Default: 0101010101010101')
@click.option('--devaddr', callback=validate_devaddr, default="01010101", type=str,
              help='ABP: DevAddr (e.g. 01010101). Default: 01010101')
@click.option('--appkey', callback=validate_key, default="2b7e151628aed2a6abf7158809cf4f3c", type=str,
              help='ABP: AppKey (e.g. 2b7e151628aed2a6abf7158809cf4f3c). Default: 2b7e151628aed2a6abf7158809cf4f3c')
@click.option('--appskey', callback=validate_key, default="2b7e151628aed2a6abf7158809cf4f3c", type=str,
              help='ABP: AppSKey (e.g. 2b7e151628aed2a6abf7158809cf4f3c). Default: 2b7e151628aed2a6abf7158809cf4f3c')
@click.option('--nwkskey', callback=validate_key, default="2b7e151628aed2a6abf7158809cf4f3c", type=str,
              help='ABP: NwkSKey (e.g. 2b7e151628aed2a6abf7158809cf4f3c). Default: 2b7e151628aed2a6abf7158809cf4f3c')
@click.option('--tas_appeui', callback=validate_eui, default="0101010101010101", type=str,
              help='Test Application Server AppEUI (e.g. 0101010101010101). Default: 0101010101010101')
def agent_mock_main(deveui, devaddr, appkey, appskey, nwkskey, tas_appeui):
    """ Entry point of the message simulator auxiliary command. This starts a message generator and waits
        for commands from the CLI to send messages to the TAS.
    """
    dev_id_dict = DeviceID(devaddr_bytes=devaddr,
                           deveui_bytes=deveui,
                           appkey_bytes=appkey,
                           appskey_bytes=appskey,
                           nwkskey_bytes=nwkskey)
    generator = gen.MessageGenerator(device_id=dev_id_dict,
                                     testserver_appeui=tas_appeui)
    print("\n\nAgent mock started and ready to interact with the Testing App Server.", flush=True)
    generator.start_consuming()


