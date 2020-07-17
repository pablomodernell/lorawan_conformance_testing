"""
This modules implements the creation and parsing of configuration information messages that the different
services of the testing platform need to exchange.
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
from utils import bytes_to_text


class DeviceID(object):
    """
    This class is used to parse the session device information.
    Session identification lorawan_parameters of an end device, base64 encoded.
    {
        "DevAddr": "ASgpnw==",
        "DevEUI": "AASjCwAa2+U=",
        "AppKey": "K34VFiiu0qar9xWICc9PPA==",
        "AppSKey": "K34VFiiu0qar9xWICc9PPA==",
        "NwkSKey": "K34VFiiu0qar9xWICc9PPA=="
    }
    """

    def __init__(self, 
                 json_device_id_str=None, 
                 devaddr_bytes=None,
                 deveui_bytes=None,
                 appkey_bytes=None,
                 appskey_bytes=None,
                 nwkskey_bytes=None):
        """
        (DeviceID, str) -> (DeviceID)
        :param json_device_id_str: string-json formatted.
        """
        if json_device_id_str:
            self.device_id_dict = json.loads(json_device_id_str)
        elif devaddr_bytes and deveui_bytes and appkey_bytes and appskey_bytes and nwkskey_bytes:
            self.device_id_dict = dict()
            self.device_id_dict["DevAddr"] = base64.b64encode(devaddr_bytes)
            self.device_id_dict["DevEUI"] = base64.b64encode(deveui_bytes)
            self.device_id_dict["AppKey"] = base64.b64encode(appkey_bytes)
            self.device_id_dict["AppSKey"] = base64.b64encode(appskey_bytes)
            self.device_id_dict["NwkSKey"] = base64.b64encode(nwkskey_bytes)
        else:
            self.device_id_dict = {
                "DevAddr": "ASgpnw==",
                "DevEUI": "AASjCwAa2+U=",
                "AppKey": "K34VFiiu0qar9xWICc9PPA==",
                "AppSKey": "K34VFiiu0qar9xWICc9PPA==",
                "NwkSKey": "K34VFiiu0qar9xWICc9PPA=="
            }

    @property
    def deveui(self):
        return base64.b64decode(self.device_id_dict["DevEUI"])

    @deveui.setter
    def deveui(self, deveui_bytes):
        self.device_id_dict["DevEUI"] = base64.b64encode(deveui_bytes).decode()

    @property
    def devaddr(self):
        return base64.b64decode(self.device_id_dict["DevAddr"])

    @devaddr.setter
    def devaddr(self, devaddr_bytes):
        self.device_id_dict["DevAddr"] = base64.b64encode(devaddr_bytes).decode()
        
    @property
    def appkey(self):
        return base64.b64decode(self.device_id_dict["AppKey"])

    @appkey.setter
    def appkey(self, appkey_bytes):
        self.device_id_dict["AppKey"] = base64.b64encode(appkey_bytes).decode()

    @property
    def appskey(self):
        return base64.b64decode(self.device_id_dict["AppSKey"])

    @appskey.setter
    def appskey(self, appskey_bytes):
        self.device_id_dict["AppSKey"] = base64.b64encode(appskey_bytes).decode()

    @property
    def nwkskey(self):
        return base64.b64decode(self.device_id_dict["NwkSKey"])

    @nwkskey.setter
    def nwkskey(self, nwkskey_bytes):
        self.device_id_dict["NwkSKey"] = base64.b64encode(nwkskey_bytes).decode()

    def __str__(self):
        """ String representation of the DeviceID, the object could be created again parsing this string."""
        return json.dumps(self.device_id_dict, indent=4, sort_keys=True)

    def to_print_str(self):
        """ Creates a human readable string with the contained information."""
        temp = "DevAddr: {DevAddr}\nDevEUI: {DevEUI}\nAppKey: {AppKey}\nAppSKey: {AppSKey}\nNwkSKey: {NwkSKey}"
        retstr = temp.format(DevAddr=bytes_to_text(self.devaddr),
                             DevEUI=bytes_to_text(self.deveui),
                             AppKey=bytes_to_text(self.appkey),
                             AppSKey=bytes_to_text(self.appskey),
                             NwkSKey=bytes_to_text(self.nwkskey))
        return retstr

