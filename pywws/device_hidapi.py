"""Low level USB interface to weather station, using hidapi.

"""

__docformat__ = "restructuredtext en"

import hidapi
import logging

class USBDevice(object):
    """Low level interface to weather station via USB.

    """

    def __init__(self, idVendor, idProduct):
        self.logger = logging.getLogger('pywws.device_hidapi.USBDevice')
        self.hid = hidapi.HID()
        devh = self.hid.open(idVendor, idProduct)
        if not devh:
            raise IOError("Weather station device not found")

    def read_data(self):
        """Receive 8 bytes from the device.

        If the read fails for any reason, :obj:`None` is returned.

        :return: the data received.

        :rtype: list(int)

        """
        byte_buf = hidapi.create_string_buffer(8)
        count = self.hid.read_timeout(byte_buf, 1200)
        if count < 0:
            raise IOError(str(self.hid.error()))
        if count < 8:
            self.logger.error('read_data failed')
            return None
        result = list()
        for i in range(count):
            result.append(ord(byte_buf.raw[i]))
        return result

    def write_data(self, buf, reportid=0):
        """Send 8 bytes to the device.

        :param buf: the data to send.

        :type buf: list(int)

        :return: success status.

        :rtype: bool

        """
        byte_buf = hidapi.create_string_buffer(len(buf) + 1)
        for i in range(len(buf)):
            byte_buf[i+1] = chr(buf[i])
        byte_buf[0] = chr(reportid)
        return self.hid.write(byte_buf)
