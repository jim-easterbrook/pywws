# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-20  pywws contributors

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Low level USB interface to weather station, using PyUSB v1.0.

Introduction
============

This module handles low level communication with the weather station
via the `PyUSB <http://sourceforge.net/apps/trac/pyusb/>`_ library
(version 1.0). It is one of several USB device modules, each of which
uses a different USB library interface. See :ref:`Installation - USB
library<dependencies-usb>` for details.

Testing
=======

Run :py:mod:`pywws.testweatherstation` with increased verbosity so it
reports which USB device access module is being used::

    python -m pywws.testweatherstation -vv
    18:28:09:pywws.weatherstation.CUSBDrive:using pywws.device_pyusb1
    0000 55 aa ff ff ff ff ff ff ff ff ff ff ff ff ff ff 05 20 01 41 11 00 00 00 81 00 00 0f 05 00 e0 51
    0020 03 27 ce 27 00 00 00 00 00 00 00 12 02 14 18 27 41 23 c8 00 00 00 46 2d 2c 01 64 80 c8 00 00 00
    0040 64 00 64 80 a0 28 80 25 a0 28 80 25 03 36 00 05 6b 00 00 0a 00 f4 01 12 00 00 00 00 00 00 00 00
    0060 00 00 49 0a 63 12 05 01 7f 00 36 01 60 80 36 01 60 80 bc 00 7b 80 95 28 12 26 6c 28 25 26 c8 01
    0080 1d 02 d8 00 de 00 ff 00 ff 00 ff 00 00 11 10 06 01 29 12 02 01 19 32 11 09 09 05 18 12 01 22 13
    00a0 14 11 11 04 15 04 11 12 17 05 12 11 09 02 15 26 12 02 11 07 05 11 09 02 15 26 12 02 11 07 05 11
    00c0 09 10 09 12 12 02 02 12 38 12 02 07 19 00 11 12 16 03 27 12 02 03 11 00 11 12 16 03 27 11 12 26
    00e0 21 32 11 12 26 21 32 12 02 06 19 57 12 02 06 19 57 12 02 06 19 57 12 02 06 19 57 12 02 06 19 57

API
===

"""

__docformat__ = "restructuredtext en"

import sys
import usb.core
import usb.util

class USBDevice(object):
    """Low level USB device access via PyUSB 1.0 library.

    :param idVendor: the USB "vendor ID" number, for example 0x1941.

    :type idVendor: int

    :param idProduct: the USB "product ID" number, for example 0x8021.

    :type idProduct: int

    """

    def __init__(self, idVendor, idProduct):
        self.dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
        if not self.dev:
            raise IOError("Weather station device not found")
        if sys.platform.startswith('linux'):
            try:
                detach = self.dev.is_kernel_driver_active(0)
            except NotImplementedError:
                detach = True
            if detach:
                try:
                    self.dev.detach_kernel_driver(0)
                except usb.core.USBError:
                    pass
        self.dev.reset()
        self.dev.set_configuration()
        usb.util.claim_interface(self.dev, 0)

    def read_data(self, size):
        """Receive data from the device.

        If the read fails for any reason, an :obj:`IOError` exception
        is raised.

        :param size: the number of bytes to read.

        :type size: int

        :return: the data received.

        :rtype: list(int)

        """
        result = self.dev.read(0x81, size, timeout=1200)
        if not result or len(result) < size:
            raise IOError('pywws.device_pyusb1.USBDevice.read_data failed')
        return list(result)

    def write_data(self, buf):
        """Send data to the device.

        If the write fails for any reason, an :obj:`IOError` exception
        is raised.

        :param buf: the data to send.

        :type buf: list(int)

        :return: success status.

        :rtype: bool

        """
        bmRequestType = usb.util.build_request_type(
            usb.util.ENDPOINT_OUT,
            usb.util.CTRL_TYPE_CLASS,
            usb.util.CTRL_RECIPIENT_INTERFACE
            )
        result = self.dev.ctrl_transfer(
            bmRequestType=bmRequestType,
            bRequest=usb.REQ_SET_CONFIGURATION,
            data_or_wLength=buf,
            wValue=0x200,
            timeout=50)
        if result != len(buf):
            raise IOError('pywws.device_pyusb1.USBDevice.write_data failed')
        return True
