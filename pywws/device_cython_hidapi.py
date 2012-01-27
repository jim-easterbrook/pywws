"""Low level USB interface to weather station, using cython-hidapi.

"""

__docformat__ = "restructuredtext en"

import hid
import logging

class USBDevice(object):
    """Low level interface to weather station via USB.

    """

    def __init__(self, idVendor, idProduct):
        self.logger = logging.getLogger('pywws.device_hidapi.USBDevice')
        self.hid = hid.device(idVendor, idProduct)
        if not self.hid:
            raise IOError("Weather station device not found")

    def read_data(self):
        """Receive 8 bytes from the device.

        If the read fails for any reason, :obj:`None` is returned.

        :return: the data received.

        :rtype: list(int)

        """
        result = self.hid.read(8)
        if len(result) < 8:
            self.logger.error('read_data failed')
        return result

    def write_data(self, buf):
        """Send 8 bytes to the device.

        :param buf: the data to send.

        :type buf: list(int)

        :return: success status.

        :rtype: bool

        """
        return self.hid.write(buf)
