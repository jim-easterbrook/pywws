"""WeatherStation.py - get data from WH1080/WH3080 compatible weather stations

Derived from wwsr.c by Michael Pendec (michael.pendec@gmail.com) and
wwsrdump.c by Svend Skafte (svend@skafte.net), modified by Dave Wells.
"""

from datetime import datetime
import logging
import math
import platform
import sys
import time
import usb

import Localisation

def dew_point(temp, hum):
    """Compute dew point, using formula from
    http://en.wikipedia.org/wiki/Dew_point."""
    if temp == None or hum == None:
        return None
    a = 17.27
    b = 237.7
    gamma = ((a * temp) / (b + temp)) + math.log(float(hum) / 100.0)
    return (b * gamma) / (a - gamma)

def wind_chill(temp, wind):
    """Compute wind chill, using formula from
    http://en.wikipedia.org/wiki/wind_chill"""
    if temp == None or wind == None:
        return None
    wind_kph = wind * 3.6
    if wind_kph <= 4.8 or temp > 10.0:
        return temp
    return min(13.12 + (temp * 0.6215) +
               (((0.3965 * temp) - 11.37) * (wind_kph ** 0.16)),
               temp)

def apparent_temp(temp, rh, wind):
    """Compute apparent temperature (real feel), using formula from
    http://www.bom.gov.au/info/thermal_stress/"""
    if temp == None or rh == None or wind == None:
        return None
    vap_press = (float(rh) / 100.0) * 6.105 * math.exp(
        17.27 * temp / (237.7 + temp))
    return temp + (0.33 * vap_press) - (0.70 * wind) - 4.00

def set_translation(trans_function):
    """Set the localisation translation function to be used by wind_dir_text
    and pressure_trend_text."""
    global _
    _ = trans_function

def get_wind_dir_text():
    """Return an array to convert wind direction integer to a string."""
    return [
        _('N'), _('NNE'), _('NE'), _('ENE'),
        _('E'), _('ESE'), _('SE'), _('SSE'),
        _('S'), _('SSW'), _('SW'), _('WSW'),
        _('W'), _('WNW'), _('NW'), _('NNW'),
        ]

def pressure_trend_text(trend):
    """Convert pressure trend to a string, see
    http://www.reedsonline.com/weather/weather-terms.htm."""
    if trend > 6.0:
        return _('rising very rapidly')
    elif trend > 3.5:
        return _('rising quickly')
    elif trend > 1.5:
        return _('rising')
    elif trend >= 0.1:
        return _('rising slowly')
    elif trend < -6.0:
        return _('falling very rapidly')
    elif trend < -3.5:
        return _('falling quickly')
    elif trend < -1.5:
        return _('falling')
    elif trend <= -0.1:
        return _('falling slowly')
    return _('steady')

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
    def _unsigned_int3(raw, offset):
        lo = raw[offset]
        md = raw[offset+1]
        hi = raw[offset+2]
        if lo == 0xFF and md == 0xFF and hi == 0xFF:
            return None
        return (hi * 256 * 256) + (md * 256) + lo
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
    def _bit_field(raw, offset):
        mask = 1
        result = []
        for i in range(8):
            result.append(raw[offset] & mask != 0)
            mask = mask << 1
        return result
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
        elif type == 'u3':
            result = _unsigned_int3(raw, pos)
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
        elif type == 'bf':
            # bit field - 'scale' is a list of bit names
            result = {}
            for k, v in zip(scale, _bit_field(raw, pos)):
                result[k] = v
            return result
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
class weather_station(object):
    """Class that represents the weather station to user program."""
    def __init__(self, ws_type='1080'):
        """Connect to weather station and prepare to read data."""
        self.logger = logging.getLogger('pywws.weather_station')
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
            if not hasattr(self.devh, 'detachKernelDriver'):
                raise RuntimeError(
                    "Please upgrade pyusb (or python-usb) to 0.4 or higher")
            try:
                self.devh.detachKernelDriver(0)
                self.devh.claimInterface(0)
            except usb.USBError:
                raise IOError("Claim interface failed")
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
        self.ws_type = ws_type
        # test 'fixed block' for data that only the 3080 stores
        if self.get_fixed_block(['max', 'illuminance', 'val']):
            if self.ws_type != '3080':
                self.logger.warning('type change %s -> %s', self.ws_type, '3080')
                self.ws_type = '3080'
        else:
            if self.ws_type != '1080':
                self.logger.warning('type change %s -> %s', self.ws_type, '1080')
                self.ws_type = '1080'
    def __del__(self):
        """Disconnect from weather station."""
        if self.devh:
            try:
                self.devh.releaseInterface()
            except usb.USBError:
                # interface was not claimed. No problem
                pass
        self.devh = None
    def live_data(self):
        # There are two things we want to synchronise to - the data is updated every
        # 48 seconds and the address is incremented every 5 minutes (or 10, 15, ...,
        # 30). Rather than getting data every second, we sleep until one of the above
        # is due. (During initialisation we get data every second anyway.)
        read_period = self.get_fixed_block(['read_period'])
        log_interval = float(read_period * 60)
        live_interval = 48.0
        old_ptr = self.current_pos()
        old_data = self.get_data(old_ptr, unbuffered=True)
        ptr_changed = False
        now = time.time()
        next_log = None
        next_live = None
        live_overdue = now + 3600.0
        while True:
            # wake up just before next reading is due
            if not next_live:
                pause = 0.0
            elif next_log:
                pause = (min(next_log, next_live) - 2) - time.time()
            elif old_data['delay'] < read_period - 1:
                pause = (next_live - 2) - time.time()
            else:
                pause = 0.0
            time.sleep(max(pause, 1.0))
            # When the pointer changes, the data is updated first. Getting the data
            # after getting the pointer makes sure that when we detect a pointer
            # change the data is correct.
            new_ptr = self.current_pos()
            new_data = self.get_data(old_ptr, unbuffered=True)
            now = time.time()
            if ptr_changed and (new_data['delay'] == None or
                                new_data['delay'] >= read_period):
                # picked up old data from new pointer, ignore it
                self.logger.info('live_data old data')
                continue
            # hide data changes caused by logging interval being reached
            if new_data['delay'] <= 0 or new_data['delay'] >= read_period:
                old_data['delay'] = new_data['delay']
            if new_data != old_data or now > live_overdue:
                if not next_live:
                    self.logger.info('live_data synchronised')
                result = dict(new_data)
                if pause > 1.0:
                    # found change immediately on waking up - probably lost sync
                    self.logger.info('live_data lost sync')
                    result = None
                    next_live = None
                    live_overdue = now + 3600.0
                elif now > live_overdue:
                    self.logger.debug('live_data overdue')
                    result['idx'] = datetime.utcfromtimestamp(int(next_live))
                    next_live += live_interval
                    live_overdue = next_live + 2.0
                else:
                    result['idx'] = datetime.utcfromtimestamp(int(now))
                    next_live = now + live_interval
                    live_overdue = next_live + 2.0
                if result:
                    yield result, old_ptr, False
                old_data = new_data
                ptr_changed = False
            if new_ptr != old_ptr:
                self.logger.debug('live_data new ptr: %06x', new_ptr)
                result = dict(new_data)
                if next_log:
                    pred = next_log + float(result['delay'] * 60) - log_interval
                if pause > 1.0:
                    # found change immediately on waking up - probably lost sync
                    self.logger.info('live_data lost log sync')
                    result = None
                    next_log = None
                elif next_log and now > pred + 3.0:
                    self.logger.info('live_data log %gs late', now - pred)
                    result['idx'] = datetime.utcfromtimestamp(int(pred))
                    next_log = pred + log_interval
                else:
                    result['idx'] = datetime.utcfromtimestamp(int(now))
                    next_log = now + log_interval
                if result:
                    yield result, old_ptr, True
                if (new_ptr != self.data_start and
                    (new_ptr - old_ptr) != self.reading_len[self.ws_type]):
                    for k in self.reading_len:
                        if (new_ptr - old_ptr) == self.reading_len[k]:
                            self.logger.warning(
                                'live_data type change %s -> %s', self.ws_type, k)
                            self.ws_type = k
                            break
                    else:
                        self.logger.error(
                                'live_data unexpected ptr change %06x -> %06x',
                                old_ptr, new_ptr)
                old_ptr = new_ptr
                ptr_changed = True
    def inc_ptr(self, ptr):
        """Get next circular buffer data pointer."""
        result = ptr + self.reading_len[self.ws_type]
        if result >= 0x10000:
            result = self.data_start
        return result
    def dec_ptr(self, ptr):
        """Get previous circular buffer data pointer."""
        result = ptr - self.reading_len[self.ws_type]
        if result < self.data_start:
            result = 0x10000 - self.reading_len[self.ws_type]
        return result
    def get_raw_data(self, ptr, unbuffered=False):
        """Get raw data from circular buffer.

        If unbuffered is false then a cached value that was obtained
        earlier may be returned."""
        if unbuffered:
            self._data_pos = None
        idx = ptr - (ptr % 0x20)
        ptr -= idx
        count = self.reading_len[self.ws_type]
        if ptr + count <= 0x20:
            # reading doesn't straddle a block boundary
            if self._data_pos != idx:
                self._data_pos = idx
                self._data_block = self._read_block(idx)
        elif self._data_pos == idx + 0x20:
            # reuse last block read
            self._data_pos = idx
            self._data_block = self._read_block(idx) + self._data_block[0:0x20]
        elif self._data_pos != idx:
            # read two blocks
            self._data_pos = idx
            self._data_block = self._read_block(idx) + self._read_block(idx + 0x20)
        elif len(self._data_block) <= 0x20:
            # 'top up' current block
            self._data_block += self._read_block(idx + 0x20)
        return self._data_block[ptr:ptr + count]
    def get_data(self, ptr, unbuffered=False):
        """Get decoded data from circular buffer.

        If unbuffered is false then a cached value that was obtained
        earlier may be returned."""
        return _decode(self.get_raw_data(ptr, unbuffered),
                       self.reading_format[self.ws_type])
    def current_pos(self):
        """Get circular buffer location where current data is being written."""
        return _decode(
            self._read_fixed_block(0x0020), self.lo_fix_format['current_pos'])
    def get_raw_fixed_block(self, unbuffered=False):
        """Get the raw "fixed block" of settings and min/max data."""
        if unbuffered or not self._fixed_block:
            self._fixed_block = self._read_fixed_block()
        return self._fixed_block
    def get_fixed_block(self, keys=[], unbuffered=False):
        """Get the decoded "fixed block" of settings and min/max data.

        A subset of the entire block can be selected by keys."""
        if unbuffered or not self._fixed_block:
            self._fixed_block = self._read_fixed_block()
        format = self.fixed_format
        # navigate down list of keys to get to wanted data
        for key in keys:
            format = format[key]
        return _decode(self._fixed_block, format)
    def get_lo_fix_block(self):
        """Get the first 64 bytes of the raw "fixed block"."""
        return _decode(self._read_fixed_block(0x0040), self.lo_fix_format)
    def _read_block(self, ptr):
        # Read block repeatedly until it's stable. This avoids getting corrupt
        # data when the block is read as the station is updating it.
        buf_1 = (ptr / 256) & 0xFF
        buf_2 = ptr & 0xFF;
        old_block = None
        while True:
            self.devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE, 9,
                                 [0xA1, buf_1, buf_2, 0x20, 0xA1, buf_1, buf_2, 0x20],
                                 value=0x200, timeout=1000)
            try:
                new_block = self.devh.interruptRead(0x81, 0x20, 1000)
                if len(new_block) == 0x20:
                    if new_block == old_block:
                        break
                    if old_block != None:
                        self.logger.debug('_read_block changing %06x', ptr)
                    old_block = new_block
            except usb.USBError, ex:
                if ex.args != ('No error',):
                    raise
        return new_block
    def _read_fixed_block(self, hi=0x0100):
        result = []
        for mempos in range(0x0000, hi, 0x0020):
            result += self._read_block(mempos)
        # check 'magic number'
        if result[:2] not in ([0x55, 0xAA], [0xFF, 0xFF], [0x55, 0x55]):
            raise IOError(
                "Unrecognised 'magic number' %02x %02x", result[0], result[1])
        return result
    def _write_byte(self, ptr, value):
        buf_1 = (ptr / 256) & 0xFF
        buf_2 = ptr & 0xFF;
        self.devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE, 9,
                             [0xA2, buf_1, buf_2, 0x20, 0xA2, value, 0, 0x20],
                             value=0x200, timeout=1000)
        while True:
            try:
                result = self.devh.interruptRead(0x81, 0x08, 1000)
                for byte in result:
                    if byte != 0xA5:
                        raise IOError('_write_byte failed')
                break
            except usb.USBError, ex:
                if ex.args != ('No error',):
                    raise
    def write_data(self, data):
        """Write a set of single bytes to the weather station. Data must be an
        array of (ptr, value) pairs."""
        # send data
        for ptr, value in data:
            self._write_byte(ptr, value)
        # set 'data changed'
        self._write_byte(self.fixed_format['data_changed'][0], 0xAA)
        # wait for station to clear 'data changed'
        while True:
            ack = _decode(
                self._read_fixed_block(0x0020), self.fixed_format['data_changed'])
            if ack == 0:
                break
            self.logger.debug('write_data waiting for ack')
            time.sleep(6)
    # Tables of "meanings" for raw weather station data. Each key
    # specifies an (offset, type, multiplier) tuple that is understood
    # by _decode.
    # depends on weather station type
    reading_format = {}
    reading_format['1080'] = {
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
    reading_format['3080'] = {
        'illuminance' : (16, 'u3', 0.1),
        'uv'          : (19, 'ub', None),
        }
    reading_format['3080'].update(reading_format['1080'])
    lo_fix_format = {
        'read_period'   : (16, 'ub', None),
        'settings_1'    : (17, 'bf', ('temp_in_F', 'temp_out_F', 'rain_in',
                                      'bit3', 'bit4', 'pressure_hPa',
                                      'pressure_inHg', 'pressure_mmHg')),
        'settings_2'    : (18, 'bf', ('wind_mps', 'wind_kmph', 'wind_knot',
                                      'wind_mph', 'wind_bft', 'bit5',
                                      'bit6', 'bit7')),
        'display_1'     : (19, 'bf', ('pressure_rel', 'wind_gust', 'clock_12hr',
                                      'date_mdy', 'time_scale_24', 'show_year',
                                      'show_day_name', 'alarm_time')),
        'display_2'     : (20, 'bf', ('temp_out_temp', 'temp_out_chill',
                                      'temp_out_dew', 'rain_hour', 'rain_day',
                                      'rain_week', 'rain_month', 'rain_total')),
        'alarm_1'       : (21, 'bf', ('bit0', 'time', 'wind_dir', 'bit3',
                                      'hum_in_lo', 'hum_in_hi',
                                      'hum_out_lo', 'hum_out_hi')),
        'alarm_2'       : (22, 'bf', ('wind_ave', 'wind_gust',
                                      'rain_hour', 'rain_day',
                                      'pressure_abs_lo', 'pressure_abs_hi',
                                      'pressure_rel_lo', 'pressure_rel_hi')),
        'alarm_3'       : (23, 'bf', ('temp_in_lo', 'temp_in_hi',
                                      'temp_out_lo', 'temp_out_hi',
                                      'wind_chill_lo', 'wind_chill_hi',
                                      'dew_point_lo', 'dew_point_hi')),
        'timezone'      : (24, 'sb', None),
        'unknown_01'    : (25, 'pb', None),
        'data_changed'  : (26, 'ub', None),
        'data_count'    : (27, 'us', None),
        'display_3'     : (29, 'bf', ('illuminance_fc', 'bit1', 'bit2', 'bit3',
                                      'bit4', 'bit5', 'bit6', 'bit7')),
        'current_pos'   : (30, 'us', None),
        'rel_pressure'  : (32, 'us', 0.1),
        'abs_pressure'  : (34, 'us', 0.1),
        'unknown_03'    : (36, 'pb', None),
        'unknown_04'    : (37, 'pb', None),
        'unknown_05'    : (38, 'pb', None),
        'unknown_06'    : (39, 'pb', None),
        'unknown_07'    : (40, 'pb', None),
        'unknown_08'    : (41, 'pb', None),
        'unknown_09'    : (42, 'pb', None),
        'date_time'     : (43, 'dt', None),
        }
    fixed_format = {
        'unknown_18'    : (97, 'pb', None),
        'unknown_19'    : (140, 'pb', None),
        'alarm'         : {
            'hum_in'        : {'hi' : (48, 'ub', None), 'lo'  : (49, 'ub', None)},
            'temp_in'       : {'hi' : (50, 'ss', 0.1), 'lo'  : (52, 'ss', 0.1)},
            'hum_out'       : {'hi' : (54, 'ub', None), 'lo'  : (55, 'ub', None)},
            'temp_out'      : {'hi' : (56, 'ss', 0.1), 'lo'  : (58, 'ss', 0.1)},
            'windchill'     : {'hi' : (60, 'ss', 0.1), 'lo'  : (62, 'ss', 0.1)},
            'dewpoint'      : {'hi' : (64, 'ss', 0.1), 'lo'  : (66, 'ss', 0.1)},
            'abs_pressure'  : {'hi' : (68, 'us', 0.1), 'lo'  : (70, 'us', 0.1)},
            'rel_pressure'  : {'hi' : (72, 'us', 0.1), 'lo'  : (74, 'us', 0.1)},
            'wind_ave'      : {'bft' : (76, 'ub', None), 'ms' : (77, 'ub', 0.1)},
            'wind_gust'     : {'bft' : (79, 'ub', None), 'ms' : (80, 'ub', 0.1)},
            'wind_dir'      : (82, 'ub', None),
            'rain'          : {'hour' : (83, 'us', 0.3), 'day'   : (85, 'us', 0.3)},
            'time'          : (87, 'tt', None),
            'illuminance'   : (89, 'u3', 0.1),
            'uv'            : (92, 'ub', None),
            },
        'max'           : {
            'uv'            : {'val' : (93, 'ub', None)},
            'illuminance'   : {'val' : (94, 'u3', 0.1)},
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
    fixed_format.update(lo_fix_format)
    # start of readings / end of fixed block
    data_start = 0x0100     # 256
    # bytes per reading, depends on weather station type
    reading_len = {
        '1080'  : 16,
        '3080'  : 20,
        }
