"""WeatherStation.py - get data from WH1080 compatible weather stations

Derived from wwsr.c by Michael Pendec (michael.pendec@gmail.com) and
wwsrdump.c by Svend Skafte (svend@skafte.net), modified by Dave Wells.
"""

import math
import platform
import usb

def dew_point(temp, hum):
    """Compute dew point, using formula from
    http://en.wikipedia.org/wiki/Dew_point."""
    a = 17.27
    b = 237.7
    gamma = ((a * temp) / (b + temp)) + math.log(float(hum) / 100.0)
    return (b * gamma) / (a - gamma)

# convert wind direction integer to string
wind_dir_text = [
    'N', 'NNE', 'NE', 'ENE',
    'E', 'ESE', 'SE', 'SSE',
    'S', 'SSW', 'SW', 'WSW',
    'W', 'WNW', 'NW', 'NNW',
    ]

def pressure_trend_text(trend):
    """Convert pressure trend to a string, see
    http://www.reedsonline.com/weather/weather-terms.htm."""
    if trend >= 0.1:
        result = 'rising'
    elif trend <= -0.1:
        result = 'falling'
    else:
        return 'steady'
    if abs(trend) > 6.0:
        return result + ' very rapidly'
    if abs(trend) > 3.5:
        return result + ' quickly'
    if abs(trend) <= 1.5:
        return result + ' slowly'
    return result

# get meaning for status integer
unknown         = 0x80
lost_connection = 0x40
unknown         = 0x20
unknown         = 0x10
unknown         = 0x08
unknown         = 0x04
unknown         = 0x02
unknown         = 0x01

# decode weather station raw data formats
def _decode(raw, format):
    def _signed_byte(raw, offset):
        res = raw[offset]
        if res == 0xFF:
            return None
        sign = 1
        if res >= 128:
            sign = -1
            res = res - 128
        return sign * res
    def _signed_short(raw, offset):
        lo = raw[offset]
        hi = raw[offset+1]
        if lo == 0xFF and hi == 0xFF:
            return None
        sign = 1
        if hi >= 128:
            sign = -1
            hi = hi - 128
        return sign * ((hi * 256) + lo)
    def _unsigned_short(raw, offset):
        lo = raw[offset]
        hi = raw[offset+1]
        if lo == 0xFF and hi == 0xFF:
            return None
        return (hi * 256) + lo
    def _bcd_decode(byte):
        hi = (byte / 16) & 0x0F
        lo = byte & 0x0F
        return (hi * 10) + lo
    def _date_time(raw, offset):
        year = _bcd_decode(raw[offset])
        month = _bcd_decode(raw[offset+1])
        day = _bcd_decode(raw[offset+2])
        hour = _bcd_decode(raw[offset+3])
        minute = _bcd_decode(raw[offset+4])
        return '%4d-%02d-%02d %02d:%02d' % (year + 2000, month, day, hour, minute)
    if not raw:
        return None
    if isinstance(format, dict):
        result = {}
        for key, value in format.items():
            result[key] = _decode(raw, value)
    else:
        pos, type, scale = format
        if type == 'ub':
            result = raw[pos]
            if result == 0xFF:
                result = None
        elif type == 'sb':
            result = _signed_byte(raw, pos)
        elif type == 'us':
            result = _unsigned_short(raw, pos)
        elif type == 'ss':
            result = _signed_short(raw, pos)
        elif type == 'dt':
            result = _date_time(raw, pos)
        elif type == 'tt':
            result = '%02d:%02d' % (_bcd_decode(raw[pos]),
                                    _bcd_decode(raw[pos+1]))
        elif type == 'pb':
            result = raw[pos]
        elif type == 'wa':
            # wind average - 12 bits split across a byte and a nibble
            result = raw[pos] + ((raw[pos+2] & 0x0F) << 8)
            if result == 0xFFF:
                result = None
        elif type == 'wg':
            # wind gust - 12 bits split across a byte and a nibble
            result = raw[pos] + ((raw[pos+1] & 0xF0) << 4)
            if result == 0xFFF:
                result = None
        else:
            raise IOError('unknown type %s' % type)
        if scale and result:
            result = float(result) * scale
    return result
def findDevice(idVendor, idProduct):
    """Find a USB device by product and vendor id."""
    for bus in usb.busses():
        for device in bus.devices:
            if device.idVendor == idVendor and device.idProduct == idProduct:
                return device
    return None
class weather_station:
    """Class that represents the weather station to user program."""
    def __init__(self):
        """Connect to weather station and prepare to read data."""
        self.devh = None
        # _open_readw
        dev = findDevice(0x1941, 0x8021)
        if not dev:
            raise IOError("Weather station device not found")
        self.devh = dev.open()
        if not self.devh:
            raise IOError("Open device failed")
        if platform.system() is 'Windows':
            self.devh.setConfiguration(1)
        try:
            self.devh.claimInterface(0)
        except usb.USBError:
            # claim interface failed, try detaching kernel driver first
            self.devh.detachKernelDriver(0)
            self.devh.claimInterface(0)
        self.devh.setAltInterface(0)
        # _init_wread
        tbuf = self.devh.getDescriptor(1, 0, 0x12)
        tbuf = self.devh.getDescriptor(2, 0, 0x09)
        tbuf = self.devh.getDescriptor(2, 0, 0x22)
        self.devh.releaseInterface()
        self.devh.setConfiguration(1)
        self.devh.claimInterface(0)
        self.devh.setAltInterface(0)
        self.devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                             0xA, 0, timeout=1000)
        tbuf = self.devh.getDescriptor(0x22, 0, 0x74)
        # init variables
        self._fixed_block = None
        self._data_block = None
        self._data_pos = None
    def __del__(self):
        """Disconnect from weather station."""
        if self.devh:
            try:
                self.devh.releaseInterface()
            except usb.USBError:
                # interface was not claimed. No problem
                pass
        self.devh = None
    def inc_ptr(self, ptr):
        """Get next circular buffer data pointer."""
        result = ptr + 0x10
        if result > 0xFFF0:
            result = 0x0100
        return result
    def dec_ptr(self, ptr):
        """Get previous circular buffer data pointer."""
        result = ptr - 0x10
        if result < 0x0100:
            result = 0xFFF0
        return result
    def get_raw_data(self, ptr, unbuffered=False):
        """Get raw data from circular buffer.

        If unbuffered is false then a cached value that was obtained
        earlier may be returned."""
        idx = ptr - (ptr % 0x20)
        if unbuffered or self._data_pos != idx:
            self._data_pos = idx
            self._data_block = self._read_block(idx)
        return self._data_block[ptr-idx:0x10+ptr-idx]
    def get_data(self, ptr, unbuffered=False):
        """Get decoded data from circular buffer.

        If unbuffered is false then a cached value that was obtained
        earlier may be returned."""
        return _decode(self.get_raw_data(ptr, unbuffered), self.reading_format)
    def current_pos(self):
        """Get circular buffer location where current data is being written."""
        return _decode(self._read_block(0x0000), self.lo_fix_format['current_pos'])
    def get_raw_fixed_block(self, unbuffered=False):
        """Get the raw "fixed block" of setting and min/max data."""
        if unbuffered or not self._fixed_block:
            self._read_fixed_block()
        return self._fixed_block
    def get_fixed_block(self, keys=[], unbuffered=False):
        """Get the decoded "fixed block" of setting and min/max data.

        A subset of the entire block can be selected by keys."""
        if unbuffered or not self._fixed_block:
            self._read_fixed_block()
        format = self.fixed_format
        # navigate down list of keys to get to wanted data
        for key in keys:
            format = format[key]
        return _decode(self._fixed_block, format)
    def get_lo_fix_block(self):
        """Get the first 64 bytes of the raw "fixed block"."""
        return _decode(self._read_block(0x0000) +
                       self._read_block(0x0020), self.lo_fix_format)
    def _read_block(self, ptr):
        buf_1 = (ptr / 256) & 0xFF
        buf_2 = ptr & 0xFF;
        self.devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE, 9,
                             [0xA1, buf_1, buf_2, 0x20, 0xA1, buf_1, buf_2, 0x20],
                             value=0x200, timeout=1000)
        return self.devh.interruptRead(0x81, 0x20, 1000)
    def _read_fixed_block(self):
        # get first line
        mempos_curr = 0x0000
        self._fixed_block = self._read_block(mempos_curr)
        # check for valid data
        if (self._fixed_block[0] == 0x55 and self._fixed_block[1] == 0xAA) or \
           (self._fixed_block[0] == 0xFF and self._fixed_block[1] == 0xFF):
            for mempos_curr in range(0x0020, 0x0100, 0x0020):
                self._fixed_block = self._fixed_block + self._read_block(mempos_curr)
        else:
            self._fixed_block = None
    # Tables of "meanings" for raw weather station data. Each key
    # specifies an (offset, type, multiplier) tuple that is understood
    # by _decode.
    reading_format = {
        'delay'        : (0, 'ub', None),
        'hum_in'       : (1, 'ub', None),
        'temp_in'      : (2, 'ss', 0.1),
        'hum_out'      : (4, 'ub', None),
        'temp_out'     : (5, 'ss', 0.1),
        'abs_pressure' : (7, 'us', 0.1),
        'wind_ave'     : (9, 'wa', 0.1),
        'wind_gust'    : (10, 'wg', 0.1),
        'wind_dir'     : (12, 'ub', None),
        'rain'         : (13, 'us', 0.3),
        'status'       : (15, 'pb', None),
        }
    lo_fix_format = {
        'read_period'   : (16, 'ub', None),
        'timezone'      : (24, 'sb', None),
        'data_count'    : (27, 'us', None),
        'current_pos'   : (30, 'us', None),
        'rel_pressure'  : (32, 'us', 0.1),
        'abs_pressure'  : (34, 'us', 0.1),
        'date_time'     : (43, 'dt', None),
        }
    fixed_format = {
        'read_period'   : (16, 'ub', None),
        'timezone'      : (24, 'sb', None),
        'data_count'    : (27, 'us', None),
        'current_pos'   : (30, 'us', None),
        'rel_pressure'  : (32, 'us', 0.1),
        'abs_pressure'  : (34, 'us', 0.1),
        'date_time'     : (43, 'dt', None),
        'alarm'         : {
            'hum_in'        : {'hi' : (48, 'ub', None), 'lo'  : (49, 'ub', None)},
            'temp_in'       : {'hi' : (50, 'ss', 0.1), 'lo'  : (52, 'ss', 0.1)},
            'hum_out'       : {'hi' : (54, 'ub', None), 'lo'  : (55, 'ub', None)},
            'temp_out'      : {'hi' : (56, 'ss', 0.1), 'lo'  : (58, 'ss', 0.1)},
            'windchill'     : {'hi' : (60, 'ss', 0.1), 'lo'  : (62, 'ss', 0.1)},
            'dewpoint'      : {'hi' : (64, 'ss', 0.1), 'lo'  : (66, 'ss', 0.1)},
            'abs_pressure'  : {'hi' : (68, 'ss', 0.1), 'lo'  : (70, 'ss', 0.1)},
            'rel_pressure'  : {'hi' : (72, 'ss', 0.1), 'lo'  : (74, 'ss', 0.1)},
            'wind_ave'      : {'bft' : (76, 'ub', None), 'ms' : (77, 'ub', 0.1)},
            'wind_gust'     : {'bft' : (79, 'ub', None), 'ms' : (80, 'ub', 0.1)},
            'wind_dir'      : (82, 'ub', None),
            'rain'          : {'hour' : (83, 'us', 0.3), 'day'   : (85, 'us', 0.3)},
            'time'          : (87, 'tt', None),
            },
        'max'           : {
            'hum_in'        : {'val' : (98, 'ub', None), 'date'   : (141, 'dt', None)},
            'hum_out'       : {'val' : (100, 'ub', None), 'date'  : (151, 'dt', None)},
            'temp_in'       : {'val' : (102, 'ss', 0.1), 'date'  : (161, 'dt', None)},
            'temp_out'      : {'val' : (106, 'ss', 0.1), 'date'  : (171, 'dt', None)},
            'windchill'     : {'val' : (110, 'ss', 0.1), 'date'  : (181, 'dt', None)},
            'dewpoint'      : {'val' : (114, 'ss', 0.1), 'date'  : (191, 'dt', None)},
            'abs_pressure'  : {'val' : (118, 'us', 0.1), 'date'  : (201, 'dt', None)},
            'rel_pressure'  : {'val' : (122, 'us', 0.1), 'date'  : (211, 'dt', None)},
            'wind_ave'      : {'val' : (126, 'us', 0.1), 'date'  : (221, 'dt', None)},
            'wind_gust'     : {'val' : (128, 'us', 0.1), 'date'  : (226, 'dt', None)},
            'rain'          : {
                'hour'          : {'val' : (130, 'us', 0.3), 'date'  : (231, 'dt', None)},
                'day'           : {'val' : (132, 'us', 0.3), 'date'  : (236, 'dt', None)},
                'week'          : {'val' : (134, 'us', 0.3), 'date'  : (241, 'dt', None)},
                'month'         : {'val' : (136, 'us', 0.3), 'date'  : (246, 'dt', None)},
                'total'         : {'val' : (138, 'us', 0.3), 'date'  : (251, 'dt', None)},
                },
            },
        'min'           : {
            'hum_in'        : {'val' : (99, 'ub', None), 'date'   : (146, 'dt', None)},
            'hum_out'       : {'val' : (101, 'ub', None), 'date'  : (156, 'dt', None)},
            'temp_in'       : {'val' : (104, 'ss', 0.1), 'date'  : (166, 'dt', None)},
            'temp_out'      : {'val' : (108, 'ss', 0.1), 'date'  : (176, 'dt', None)},
            'windchill'     : {'val' : (112, 'ss', 0.1), 'date'  : (186, 'dt', None)},
            'dewpoint'      : {'val' : (116, 'ss', 0.1), 'date'  : (196, 'dt', None)},
            'abs_pressure'  : {'val' : (120, 'us', 0.1), 'date'  : (206, 'dt', None)},
            'rel_pressure'  : {'val' : (124, 'us', 0.1), 'date'  : (216, 'dt', None)},
            },
        }