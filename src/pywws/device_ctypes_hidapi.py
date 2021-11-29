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

"""Low level USB interface to weather station, using ctypes to access hidapi.

Introduction
============

This module handles low level communication with the weather station
via `ctypes <http://docs.python.org/2/library/ctypes.html>`_ and the
`hidapi <https://github.com/signal11/hidapi>`_ library. It is one of
several USB device modules, each of which uses a different USB library
interface. See :ref:`Installation - USB library<dependencies-usb>` for
details.


Testing
=======

Run :py:mod:`pywws.testweatherstation` with increased verbosity so it
reports which USB device access module is being used::

    python -m pywws.testweatherstation -vv
    18:10:27:pywws.WeatherStation.CUSBDrive:using pywws.device_ctypes_hidapi
    0000 55 aa ff ff ff ff ff ff ff ff ff ff ff ff ff ff 05 20 01 51 11 00 00 00 81 00 00 07 01 00 d0 56
    0020 61 1c 61 1c 00 00 00 00 00 00 00 12 02 14 18 09 41 23 c8 00 32 80 47 2d 2c 01 2c 81 5e 01 1e 80
    0040 a0 00 c8 80 a0 28 80 25 a0 28 80 25 03 36 00 05 6b 00 00 0a 00 f4 01 18 00 00 00 00 00 00 00 00
    0060 00 00 54 1c 63 0a 2f 01 71 00 7a 01 59 80 7a 01 59 80 e4 00 f5 ff 69 54 00 00 fe ff 00 00 b3 01
    0080 0c 02 d0 ff d3 ff 5a 24 d2 24 dc 17 00 11 09 06 15 40 10 03 07 22 18 10 08 11 08 30 11 03 07 12
    00a0 36 08 07 24 17 17 11 02 28 10 10 09 06 30 14 29 12 02 11 06 57 09 06 30 14 29 12 02 11 06 57 08
    00c0 08 31 14 30 12 02 14 18 04 12 02 01 10 12 11 09 13 17 19 11 08 21 16 53 11 09 13 17 19 12 01 18
    00e0 07 17 10 02 22 11 06 11 11 06 13 12 11 11 06 13 12 11 11 10 11 38 11 11 10 11 38 10 02 22 14 43

API
===

"""

__docformat__ = "restructuredtext en"

import ctypes
from ctypes.util import find_library
import sys

if 'sphinx' in sys.modules:
    # building documentation, don't need to import hidapi
    pass
else:
    # open hidapi shared library
    path = find_library('hidapi')
    if not path:
        path = find_library('hidapi-libusb')
    if not path:
        path = find_library('hidapi-hidraw')
    if not path:
        raise ImportError('Cannot find hidapi library')
    hidapi = ctypes.CDLL(path)
    hidapi.hid_open.argtypes = [
        ctypes.c_ushort, ctypes.c_ushort, ctypes.c_wchar_p]
    hidapi.hid_open.restype = ctypes.c_void_p
    hidapi.hid_read_timeout.argtypes = [
        ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
    hidapi.hid_write.argtypes = [
        ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]

class USBDevice(object):
    """Low level USB device access via hidapi library.

    :param idVendor: the USB "vendor ID" number, for example 0x1941.

    :type idVendor: int

    :param idProduct: the USB "product ID" number, for example 0x8021.

    :type idProduct: int

    """

    def __init__(self, vendor_id, product_id):
        self.device = hidapi.hid_open(vendor_id, product_id, None)
        if not self.device:
            raise IOError("Weather station device not found")
        # flush any unread input
        try:
            self.read_data(32)
        except IOError:
            pass

    def read_data(self, size):
        """Receive data from the device.

        If the read fails for any reason, an :obj:`IOError` exception
        is raised.

        :param size: the number of bytes to read.

        :type size: int

        :return: the data received.

        :rtype: list(int)

        """
        result = list()
        data = ctypes.create_string_buffer(8)
        while size > 0:
            length = min(size, 8)
            n = hidapi.hid_read_timeout(self.device, data, length, 100)
            if n <= 0:
                raise IOError(
                    'pywws.device_ctypes_hidapi.USBDevice.read_data failed')
            for i in range(n):
                result.append(ord(data[i]))
            size -= n
        return result

    def write_data(self, buf):
        """Send data to the device.

        :param buf: the data to send.

        :type buf: list(int)

        :return: success status.

        :rtype: bool

        """
        data = bytes(buf)
        size = len(data)
        if hidapi.hid_write(self.device, ctypes.c_char_p(data), size) != size:
            raise IOError(
                'pywws.device_ctypes_hidapi.USBDevice.write_data failed')
        return True
