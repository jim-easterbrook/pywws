"""Low level USB interface to weather station, using libusb.

"""

__docformat__ = "restructuredtext en"

import logging
import platform
import usb

class USBDevice(object):
    """Low level interface to weather station via USB.

    """

    def __init__(self, idVendor, idProduct):
        self.logger = logging.getLogger('pywws.device_libusb.USBDevice')
        dev = self._find_device(idVendor, idProduct)
        if not dev:
            raise IOError("Weather station device not found")
        self.devh = dev.open()
        if not self.devh:
            raise IOError("Open device failed")
##        if platform.system() is 'Windows':
##            self.devh.setConfiguration(1)
        try:
            self.devh.claimInterface(0)
        except usb.USBError:
            # claim interface failed, try detaching kernel driver first
            if not hasattr(self.devh, 'detachKernelDriver'):
                raise RuntimeError(
                    "Please upgrade pyusb (or python-usb) to 0.4 or higher")
            try:
                self.devh.detachKernelDriver(0)
                self.devh.claimInterface(0)
            except usb.USBError:
                raise IOError("Claim interface failed")

    def __del__(self):
        if self.devh:
            try:
                self.devh.releaseInterface()
            except usb.USBError:
                # interface was not claimed. No problem
                pass

    def _find_device(self, idVendor, idProduct):
        """Find a USB device by product and vendor id."""
        for bus in usb.busses():
            for device in bus.devices:
                if (device.idVendor == idVendor and
                    device.idProduct == idProduct):
                    return device
        return None

    def read_data(self):
        """Receive 8 bytes from the device.

        If the read fails for any reason, :obj:`None` is returned.

        :return: the data received.

        :rtype: list(int)

        """
        result = self.devh.interruptRead(0x81, 8, 1200)
        if result is None or len(result) < 8:
            self.logger.error('_read_data failed')
            return None
        return result

    def write_data(self, buf):
        """Send 8 bytes to the device.

        :param buf: the data to send.

        :type buf: list(int)

        :return: success status.

        :rtype: bool

        """
        result = self.devh.controlMsg(
            usb.ENDPOINT_OUT + usb.TYPE_CLASS + usb.RECIP_INTERFACE,
            usb.REQ_SET_CONFIGURATION, buf, value=0x200, timeout=50)
        if result != 8:
            self.logger.error('_write_data failed')
            return False
        return True
