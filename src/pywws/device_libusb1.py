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

"""Low level USB interface to weather station, using python-libusb1.

Introduction
============

This module handles low level communication with the weather station
via the `python-libusb1
<https://github.com/vpelletier/python-libusb1>`_ library. It is one of
several USB device modules, each of which uses a different USB library
interface. See :ref:`Installation - USB library<dependencies-usb>` for
details.

Testing
=======

Run :py:mod:`pywws-testweatherstation <pywws.testweatherstation>` with
increased verbosity so it reports which USB device access module is
being used::

    pywws-testweatherstation -vv
    11:30:35:pywws.logger:pywws version 15.01.0
    11:30:35:pywws.logger:Python version 3.3.5 (default, Mar 27 2014, 17:16:46) [GCC]
    11:30:35:pywws.weatherstation.CUSBDrive:using pywws.device_libusb1
    0000 55 aa ff ff ff ff ff ff ff ff ff ff ff ff ff ff 05 20 01 41 11 00 00 00 81 7f 00 f0 0f 00 50 04
    0020 f9 25 74 26 00 00 00 00 00 00 00 15 01 15 11 31 41 23 c8 00 00 00 46 2d 2c 01 64 80 c8 00 00 00
    0040 64 00 64 80 a0 28 80 25 a0 28 80 25 03 36 00 05 6b 00 00 0a 00 f4 01 12 00 00 00 00 00 00 00 00
    0060 00 00 5a 0a 63 0a 41 01 70 00 dc 01 08 81 dc 01 c5 81 68 01 75 81 95 28 e0 25 24 29 d9 25 fd 02
    0080 b9 02 f4 ff fd ff 85 ff 91 ff 6c 09 00 14 10 19 06 29 12 02 01 19 32 11 09 09 05 18 12 03 28 13
    00a0 00 13 07 19 18 28 13 01 18 23 21 13 09 24 13 02 13 09 24 13 33 13 09 24 13 02 12 07 28 12 50 13
    00c0 09 24 13 02 13 10 14 16 18 12 02 07 19 00 14 02 14 22 39 13 01 04 10 28 15 01 15 03 48 12 03 10
    00e0 22 02 13 01 30 21 24 12 07 28 11 59 13 03 06 06 43 12 04 13 00 04 12 04 13 00 04 12 07 31 03 34

API
===

"""

__docformat__ = "restructuredtext en"

import libusb1
import sys
import usb1

class USBDevice(object):
    """Low level USB device access via python-libusb1 library.

    :param idVendor: the USB "vendor ID" number, for example 0x1941.

    :type idVendor: int

    :param idProduct: the USB "product ID" number, for example 0x8021.

    :type idProduct: int

    """

    def __init__(self, idVendor, idProduct):
        self.context = usb1.USBContext()
        self.dev = self.context.openByVendorIDAndProductID(idVendor, idProduct)
        if not self.dev:
            raise IOError("Weather station device not found")
        if sys.platform.startswith('linux'):
            if self.dev.kernelDriverActive(0):
                self.dev.detachKernelDriver(0)
        self.dev.resetDevice()
        self.dev.claimInterface(0)

    def read_data(self, size):
        """Receive data from the device.

        If the read fails for any reason, an :obj:`IOError` exception
        is raised.

        :param size: the number of bytes to read.

        :type size: int

        :return: the data received.

        :rtype: list(int)

        """
        result = self.dev.bulkRead(0x81, size, timeout=1200)
        if not result or len(result) < size:
            raise IOError('pywws.device_libusb1.USBDevice.read_data failed')
        # Python2 libusb1 version 1.5 and earlier returns a string
        if not isinstance(result[0], int):
            result = map(ord, result)
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
        if sys.version_info[0] < 3:
            str_buf = ''.join(map(chr, buf))
        else:
            str_buf = bytes(buf)
        result = self.dev.controlWrite(
            libusb1.LIBUSB_ENDPOINT_OUT | libusb1.LIBUSB_TYPE_CLASS |
            libusb1.LIBUSB_RECIPIENT_INTERFACE,
            libusb1.LIBUSB_REQUEST_SET_CONFIGURATION,
            0x200, 0, str_buf, timeout=50)
        if result != len(buf):
            raise IOError('pywws.device_libusb1.USBDevice.write_data failed')
        return True
