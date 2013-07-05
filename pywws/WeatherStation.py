# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

"""Get data from WH1080/WH3080 compatible weather stations.

Derived from wwsr.c by Michael Pendec (michael.pendec@gmail.com),
wwsrdump.c by Svend Skafte (svend@skafte.net), modified by Dave Wells,
and other sources.

Introduction
------------

This is the module that actually talks to the weather station base
unit. I don't have much understanding of USB, so copied a lot from
Michael Pendec's C program wwsr.

The weather station memory has two parts: a "fixed block" of 256 bytes
and a circular buffer of 65280 bytes. As each weather reading takes 16
bytes the station can store 4080 readings, or 14 days of 5-minute
interval readings. (The 3080 type stations store 20 bytes per reading,
so store a maximum of 3264.) As data is read in 32-byte chunks, but
each weather reading is 16 or 20 bytes, a small cache is used to
reduce USB traffic. The caching behaviour can be over-ridden with the
``unbuffered`` parameter to ``get_data`` and ``get_raw_data``.

Decoding the data is controlled by the static dictionaries
``reading_format``, ``lo_fix_format`` and ``fixed_format``. The keys
are names of data items and the values can be an ``(offset, type,
multiplier)`` tuple or another dictionary. So, for example, the
reading_format dictionary entry ``'rain' : (13, 'us', 0.3)`` means
that the rain value is an unsigned short (two bytes), 13 bytes from
the start of the block, and should be multiplied by 0.3 to get a
useful value.

The use of nested dictionaries in the ``fixed_format`` dictionary
allows useful subsets of data to be decoded. For example, to decode
the entire block ``get_fixed_block`` is called with no parameters::

  ws = WeatherStation.weather_station()
  print ws.get_fixed_block()

To get the stored minimum external temperature, ``get_fixed_block`` is
called with a sequence of keys::

  ws = WeatherStation.weather_station()
  print ws.get_fixed_block(['min', 'temp_out', 'val'])

Often there is no requirement to read and decode the entire fixed
block, as its first 64 bytes contain the most useful data: the
interval between stored readings, the buffer address where the current
reading is stored, and the current date & time. The
``get_lo_fix_block`` method provides easy access to these.

For more examples of using the WeatherStation module, see the
TestWeatherStation program.

Detailed API
------------

"""

__docformat__ = "restructuredtext en"

from datetime import datetime
import logging
import sys
import time

from pywws import Localisation
USBDevice = None
if not USBDevice:
    try:
        from pywws.device_ctypes_hidapi import USBDevice
    except ImportError:
        pass
if not USBDevice:
    try:
        from pywws.device_cython_hidapi import USBDevice
    except ImportError:
        pass
if not USBDevice:
    try:
        from pywws.device_pyusb1 import USBDevice
    except ImportError:
        pass
if not USBDevice:
    from pywws.device_pyusb import USBDevice

# get meaning for status integer
rain_overflow   = 0x80
lost_connection = 0x40
unknown         = 0x20
unknown         = 0x10
unknown         = 0x08
unknown         = 0x04
unknown         = 0x02
unknown         = 0x01

def decode_status(status):
    result = {}
    for key, mask in (('rain_overflow',   0x80),
                      ('lost_connection', 0x40),
                      ('unknown',         0x3f),
                      ):
        result[key] = status & mask
    return result

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
        hi = (byte // 16) & 0x0F
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

class CUSBDrive(object):
    """Low level interface to weather station via USB.

    Loosely modeled on a C++ class obtained from
    http://site.ambientweatherstore.com/easyweather/ws_1080_2080_protocol.zip.
    I don't know the provenance of this, but it looks as if it may
    have come from the manufacturer.

    """
    EndMark          = 0x20
    ReadCommand      = 0xA1
    WriteCommand     = 0xA0
    WriteCommandWord = 0xA2

    def __init__(self):
        self.logger = logging.getLogger('pywws.WeatherStation.CUSBDrive')
        self.logger.info('using %s', USBDevice.__module__)
        self.dev = USBDevice(0x1941, 0x8021)

    def read_block(self, address):
        """Read 32 bytes from the weather station.

        If the read fails for any reason, :obj:`None` is returned.

        :param address: address to read from.

        :type address: int

        :return: the data from the weather station.

        :rtype: list(int)

        """
        buf = [
            self.ReadCommand,
            address // 256,
            address % 256,
            self.EndMark,
            self.ReadCommand,
            address // 256,
            address % 256,
            self.EndMark,
            ]
        if not self.dev.write_data(buf):
            return None
        return self.dev.read_data(32)

    def write_byte(self, address, data):
        """Write a single byte to the weather station.

        :param address: address to write to.

        :type address: int

        :param data: the value to write.

        :type data: int

        :return: success status.

        :rtype: bool

        """
        buf = [
            self.WriteCommandWord,
            address // 256,
            address % 256,
            self.EndMark,
            self.WriteCommandWord,
            data,
            0,
            self.EndMark,
            ]
        if not self.dev.write_data(buf):
            return False
        buf = self.dev.read_data(8)
        if buf is None:
            return False
        for byte in buf:
            if byte != 0xA5:
                return False
        return True

class weather_station(object):
    """Class that represents the weather station to user program."""
    # avoid USB activity this number of seconds each side of time when
    # station screen is believed to be writing to the memory
    avoid = 3.0
    # minimum interval between polling for data change
    min_pause = 0.5
    def __init__(self, ws_type='1080', params=None, status=None):
        """Connect to weather station and prepare to read data."""
        self.logger = logging.getLogger('pywws.weather_station')
        # create basic IO object
        self.cusb = CUSBDrive()
        # init variables
        self.params = params
        self.status = status
        self._fixed_block = None
        self._data_block = None
        self._data_pos = None
        self._current_ptr = None
        if self.params:
            self.params.unset('fixed', 'station clock')
            self.params.unset('fixed', 'sensor clock')
        if self.status:
            self._station_clock = eval(
                self.status.get('clock', 'station', 'None'))
            self._sensor_clock = eval(
                self.status.get('clock', 'sensor', 'None'))
        else:
            self._station_clock = None
            self._sensor_clock = None
        self.ws_type = ws_type

    def live_data(self, logged_only=False):
        # There are two things we want to synchronise to - the data is
        # updated every 48 seconds and the address is incremented
        # every 5 minutes (or 10, 15, ..., 30). Rather than getting
        # data every second or two, we sleep until one of the above is
        # due. (During initialisation we get data every two seconds
        # anyway.)
        read_period = self.get_fixed_block(['read_period'])
        log_interval = float(read_period * 60)
        live_interval = 48.0
        old_ptr = self.current_pos()
        old_data = self.get_data(old_ptr, unbuffered=True)
        now = time.time()
        if self._sensor_clock:
            next_live = now
            next_live -= (next_live - self._sensor_clock) % live_interval
            next_live += live_interval
        else:
            next_live = None
        if self._station_clock and next_live:
            # set next_log
            next_log = next_live - live_interval
            next_log -= (next_log - self._station_clock) % 60
            next_log -= old_data['delay'] * 60
            next_log += log_interval
        else:
            next_log = None
            self._station_clock = None
        ptr_time = 0
        data_time = 0
        last_log = now - (old_data['delay'] * 60)
        last_status = None
        while True:
            if not self._station_clock:
                next_log = None
            if not self._sensor_clock:
                next_live = None
            now = time.time()
            # wake up just before next reading is due
            advance = now + max(self.avoid, self.min_pause) + self.min_pause
            pause = 600.0
            if next_live:
                if not logged_only:
                    pause = min(pause, next_live - advance)
            else:
                pause = self.min_pause
            if next_log:
                pause = min(pause, next_log - advance)
            elif old_data['delay'] < read_period - 1:
                pause = min(
                    pause, ((read_period - old_data['delay']) * 60.0) - 110.0)
            else:
                pause = self.min_pause
            pause = max(pause, self.min_pause)
            self.logger.debug(
                'delay %s, pause %g', str(old_data['delay']), pause)
            time.sleep(pause)
            # get new data
            last_data_time = data_time
            new_data = self.get_data(old_ptr, unbuffered=True)
            data_time = time.time()
            # log any change of status
            if new_data['status'] != last_status:
                self.logger.warning(
                    'status %s', str(decode_status(new_data['status'])))
            last_status = new_data['status']
            # 'good' time stamp if we haven't just woken up from long
            # pause and data read wasn't delayed
            valid_time = data_time - last_data_time < (self.min_pause * 2.0) - 0.1
            # make sure changes because of logging interval aren't
            # mistaken for new live data
            if new_data['delay'] >= read_period:
                for key in ('delay', 'hum_in', 'temp_in', 'abs_pressure'):
                    old_data[key] = new_data[key]
            # ignore solar data which changes every 60 seconds
            if self.ws_type == '3080':
                for key in ('illuminance', 'uv'):
                    old_data[key] = new_data[key]
            if new_data != old_data:
                self.logger.debug('live_data new data')
                result = dict(new_data)
                if valid_time:
                    # data has just changed, so definitely at a 48s update time
                    self._sensor_clock = data_time
                    self.logger.warning(
                        'setting sensor clock %g', data_time % live_interval)
                    if self.status:
                        self.status.set(
                            'clock', 'sensor', str(self._sensor_clock))
                    if not next_live:
                        self.logger.warning('live_data live synchronised')
                    else:
                        self.logger.error('unexpected sensor clock setting')
                    next_live = data_time
                elif next_live and data_time < next_live - self.min_pause:
                    self.logger.warning(
                        'live_data lost sync %g', data_time - next_live)
                    next_live = None
                    self._sensor_clock = None
                if next_live and not logged_only:
                    while data_time > next_live + live_interval:
                        self.logger.info('live_data missed')
                        next_live += live_interval
                    result['idx'] = datetime.utcfromtimestamp(int(next_live))
                    next_live += live_interval
                    yield result, old_ptr, False
                old_data = new_data
            # get new pointer
            if old_data['delay'] < read_period - 1:
                continue
            last_ptr_time = ptr_time
            new_ptr = self.current_pos()
            ptr_time = time.time()
            valid_time = ptr_time - last_ptr_time < (self.min_pause * 2.0) - 0.1
            if new_ptr != old_ptr:
                self.logger.debug('live_data new ptr: %06x', new_ptr)
                last_log = ptr_time
                # re-read data, to be absolutely sure it's the last
                # logged data before the pointer was updated
                new_data = self.get_data(old_ptr, unbuffered=True)
                result = dict(new_data)
                if valid_time:
                    # pointer has just changed, so definitely at a logging time
                    self._station_clock = ptr_time
                    self.logger.warning(
                        'setting station clock %g', ptr_time % 60.0)
                    if self.status:
                        self.status.set(
                            'clock', 'station', str(self._station_clock))
                    if not next_log:
                        self.logger.warning('live_data log synchronised')
                    next_log = ptr_time
                elif next_log and ptr_time < next_log - self.min_pause:
                    self.logger.warning(
                        'live_data lost log sync %g', ptr_time - next_log)
                    next_log = None
                    self._station_clock = None
                if next_log:
                    result['idx'] = datetime.utcfromtimestamp(int(next_log))
                    next_log += log_interval
                    yield result, old_ptr, True
                if new_ptr != self.inc_ptr(old_ptr):
                    self.logger.error(
                        'live_data unexpected ptr change %06x -> %06x',
                        old_ptr, new_ptr)
                old_ptr = new_ptr
                old_data['delay'] = 0
                data_time = 0
            elif ptr_time > last_log + ((new_data['delay'] + 2) * 60):
                # if station stops logging data, don't keep reading
                # USB until it locks up
                raise IOError('station is not logging data')
            elif valid_time and next_log and ptr_time > next_log + 6.0:
                self.logger.warning('live_data log extended')
                next_log += 60.0

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
        # round down ptr to a 'block boundary'
        idx = ptr - (ptr % 0x20)
        ptr -= idx
        count = self.reading_len[self.ws_type]
        if self._data_pos == idx:
            # cache contains useful data
            result = self._data_block[ptr:ptr + count]
            if len(result) >= count:
                return result
        else:
            result = list()
        if ptr + count > 0x20:
            # need part of next block, which may be in cache
            if self._data_pos != idx + 0x20:
                self._data_pos = idx + 0x20
                self._data_block = self._read_block(self._data_pos)
            result += self._data_block[0:ptr + count - 0x20]
            if len(result) >= count:
                return result
        # read current block
        self._data_pos = idx
        self._data_block = self._read_block(self._data_pos)
        result = self._data_block[ptr:ptr + count] + result
        return result

    def get_data(self, ptr, unbuffered=False):
        """Get decoded data from circular buffer.

        If unbuffered is false then a cached value that was obtained
        earlier may be returned."""
        return _decode(self.get_raw_data(ptr, unbuffered),
                       self.reading_format[self.ws_type])

    def current_pos(self):
        """Get circular buffer location where current data is being written."""
        new_ptr = _decode(
            self._read_fixed_block(0x0020), self.lo_fix_format['current_pos'])
        if new_ptr == self._current_ptr:
            return self._current_ptr
        if self._current_ptr and new_ptr != self.inc_ptr(self._current_ptr):
            for k in self.reading_len:
                if (new_ptr - self._current_ptr) == self.reading_len[k]:
                    self.logger.warning(
                        'type change %s -> %s', self.ws_type, k)
                    self.ws_type = k
                    break
        self._current_ptr = new_ptr
        return self._current_ptr

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

    def _wait_for_station(self):
        # avoid times when station is writing to memory
        while True:
            pause = 60.0
            if self._station_clock:
                phase = time.time() - self._station_clock
                if phase > 24 * 3600:
                    # station clock was last measured a day ago, so reset it
                    self._station_clock = None
                else:
                    pause = min(pause, (self.avoid - phase) % 60)
            if self._sensor_clock:
                phase = time.time() - self._sensor_clock
                if phase > 24 * 3600:
                    # sensor clock was last measured a day ago, so reset it
                    self._sensor_clock = None
                else:
                    pause = min(pause, (self.avoid - phase) % 48)
            if pause > self.avoid * 2.0:
                return
            self.logger.debug('avoid %s', str(pause))
            time.sleep(pause)

    def _read_block(self, ptr, retry=True):
        # Read block repeatedly until it's stable. This avoids getting corrupt
        # data when the block is read as the station is updating it.
        old_block = None
        while True:
            self._wait_for_station()
            new_block = self.cusb.read_block(ptr)
            if new_block:
                if (new_block == old_block) or not retry:
                    break
                if old_block:
                    self.logger.debug('_read_block changing %06x', ptr)
                old_block = new_block
        return new_block

    def _read_fixed_block(self, hi=0x0100):
        result = []
        for mempos in range(0x0000, hi, 0x0020):
            result += self._read_block(mempos)
        # check 'magic number'
        if result[:2] not in ([0x55, 0xAA], [0xFF, 0xFF],
                              [0x55, 0x55], [0xC4, 0x00]):
            self.logger.critical(
                "Unrecognised 'magic number' %02x %02x", result[0], result[1])
        return result

    def _write_byte(self, ptr, value):
        self._wait_for_station()
        if not self.cusb.write_byte(ptr, value):
            raise IOError('_write_byte failed')

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
        }
    fixed_format = {
        'rel_pressure'  : (32, 'us', 0.1),
        'abs_pressure'  : (34, 'us', 0.1),
        'lux_wm2_coeff' : (36, 'us', 0.1),
        'date_time'     : (43, 'dt', None),
        'unknown_18'    : (97, 'pb', None),
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
