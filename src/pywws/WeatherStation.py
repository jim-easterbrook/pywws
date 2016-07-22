# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-16  pywws contributors

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
``_reading_format``, ``lo_fix_format`` and ``fixed_format``. The keys
are names of data items and the values can be an ``(offset, type,
multiplier)`` tuple or another dictionary. So, for example, the
_reading_format dictionary entry ``'rain' : (13, 'us', 0.3)`` means
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

from __future__ import absolute_import

__docformat__ = "restructuredtext en"

from datetime import datetime
import logging
import sys
import time

from pywws import Localisation
for module_name in ('device_libusb1', 'device_pyusb1', 'device_pyusb',
                    'device_ctypes_hidapi', 'device_cython_hidapi'):
    try:
        module = __import__(module_name, globals(), locals(), level=1)
        USBDevice = getattr(module, 'USBDevice')
        break
    except ImportError:
        pass
else:
    raise ImportError('No USB library found')

def decode_status(status):
    result = {}
    for key, mask in (('invalid_wind_dir', 0x800),
                      ('rain_overflow',    0x080),
                      ('lost_connection',  0x040),
                      ('unknown',          0x73f),
                      ):
        result[key] = status & mask
    return result

# decode weather station raw data formats
def _plain_byte(raw, offset):
    return raw[offset]

def _unsigned_byte(raw, offset):
    res = raw[offset]
    if res == 0xFF:
        return None
    return res

def _signed_byte(raw, offset):
    res = raw[offset]
    if res == 0xFF:
        return None
    if res >= 128:
        return 128 - res
    return res

def _unsigned_short(raw, offset):
    lo = raw[offset]
    hi = raw[offset+1]
    if lo == 0xFF and hi == 0xFF:
        return None
    return (hi * 256) + lo

def _signed_short(raw, offset):
    lo = raw[offset]
    hi = raw[offset+1]
    if lo == 0xFF and hi == 0xFF:
        return None
    if hi >= 128:
        return ((128 - hi) * 256) - lo
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

def _time(raw, offset):
    hour = _bcd_decode(raw[offset])
    minute = _bcd_decode(raw[offset+1])
    return '%02d:%02d' % (hour, minute)

def _wind_ave(raw, offset):
    # wind average - 12 bits split across a byte and a nibble
    result = raw[offset] + ((raw[offset+2] & 0x0F) << 8)
    if result == 0xFFF:
        result = None
    return result

def _wind_gust(raw, offset):
    # wind gust - 12 bits split across a byte and a nibble
    result = raw[offset] + ((raw[offset+1] & 0xF0) << 4)
    if result == 0xFFF:
        result = None
    return result

def _bit_field(raw, offset):
    # convert byte to list of 8 booleans
    mask = 1
    result = []
    for i in range(8):
        result.append(raw[offset] & mask != 0)
        mask = mask << 1
    return result

_decoders = {
    'pb' : _plain_byte,
    'ub' : _unsigned_byte,
    'sb' : _signed_byte,
    'us' : _unsigned_short,
    'ss' : _signed_short,
    'u3' : _unsigned_int3,
    'dt' : _date_time,
    'tt' : _time,
    'wa' : _wind_ave,
    'wg' : _wind_gust,
    'bf' : _bit_field,
    }

def _decode(raw, format):
    if not raw:
        return None
    if isinstance(format, dict):
        result = {}
        for key, value in format.items():
            result[key] = _decode(raw, value)
    else:
        pos, type, scale = format
        result = _decoders[type](raw, pos)
        if type == 'bf':
            # bit field - 'scale' is a list of bit names
            result = dict(zip(scale, result))
        elif scale and result:
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

class DriftingClock(object):
    def __init__(self, logger, name, status, period, margin):
        self.logger = logger
        self.name = name
        self.status = status
        self.period = period
        self.margin = margin
        if self.status:
            self.clock = eval(
                self.status.get('clock', self.name, 'None'))
            self.drift = eval(
                self.status.get('clock', '%s drift' % self.name, '0.0'))
        else:
            self.clock = None
            self.drift = 0.0
        self._set_real_period()
        self.old_clock = self.clock

    def _set_real_period(self):
        self._real_period = self.period * (1.0 + (self.drift / (24.0 * 3600.0)))

    def before(self, now):
        if not self.clock:
            return None
        error = (now - self.clock) % self._real_period
        return now - error

    def avoid(self):
        if not self.clock:
            return 1000.0
        now = time.time()
        phase = now - self.clock
        if phase > 24 * 3600:
            # clock was last measured a day ago, so reset it
            self.clock = None
            return 1000.0
        return (self.margin - phase) % self._real_period

    def set_clock(self, now):
        if self.clock:
            diff = (now - self.clock) % self._real_period
            if diff < 2.0 or diff > self._real_period - 2.0:
                return
            self.logger.error('unexpected %s clock change', self.name)
        self.clock = now
        self.logger.warning('setting %s clock %g', self.name, now % self.period)
        if self.status:
            self.status.set('clock', self.name, str(self.clock))
        if self.old_clock:
            diff = now - self.old_clock
            if diff < 8 * 3600:
                # drift measurement needs more than 8 hours gap
                return
            drift = diff % self.period
            if drift > self.period / 2:
                drift -= self.period
            drift = (float(drift) * 24.0 * 3600.0 / float(diff))
            self.drift += max(min(drift - self.drift, 3.0), -3.0) / 4.0
            self._set_real_period()
            self.logger.warning(
                '%s clock drift %g %g', self.name, drift, self.drift)
            if self.status:
                self.status.set(
                    'clock', '%s drift' % self.name, str(self.drift))
        self.old_clock = self.clock

    def invalidate(self):
        self.clock = None

class weather_station(object):
    """Class that represents the weather station to user program."""
    # minimum interval between polling for data change
    min_pause = 0.5
    # margin of error for various decisions
    margin = (min_pause * 2.0) - 0.1
    def __init__(self, ws_type='1080', status=None, avoid=3.0):
        """Connect to weather station and prepare to read data."""
        self.logger = logging.getLogger('pywws.weather_station')
        # create basic IO object
        self.cusb = CUSBDrive()
        # init variables
        self.status = status
        self.avoid = max(avoid, 0.0)
        self._fixed_block = None
        self._data_block = None
        self._data_pos = None
        self._current_ptr = None
        self._station_clock = DriftingClock(
            self.logger, 'station', self.status, 60, self.avoid)
        self._sensor_clock = DriftingClock(
            self.logger, 'sensor', self.status, 48, self.avoid)
        self.ws_type = ws_type

    def live_data(self, logged_only=False):
        # There are two things we want to synchronise to - the data is
        # updated every 48 seconds and the address is incremented
        # every 5 minutes (or 10, 15, ..., 30). Rather than getting
        # data every second or two, we sleep until one of the above is
        # due. (During initialisation we get data every half second
        # anyway.)
        read_period = self.get_fixed_block(['read_period'])
        self.logger.debug('read period %d', read_period)
        log_interval = float(read_period * 60)
        live_interval = 48.0
        old_ptr = self.current_pos()
        old_data = self.get_data(old_ptr, unbuffered=True)
        now = time.time()
        next_live = self._sensor_clock.before(now + live_interval)
        if next_live:
            now = next_live - live_interval
        else:
            now -= live_interval
        last_log = now - (old_data['delay'] * 60.0)
        next_log = self._station_clock.before(last_log + log_interval)
        ptr_time = 0
        data_time = 0
        last_status = decode_status(0)
        while True:
            # sleep until just before next reading is due
            now = time.time()
            advance = now + max(self.avoid, self.min_pause) + self.min_pause
            if next_live:
                pause = next_live - advance
            else:
                pause = self.min_pause
            if next_log:
                pause = min(pause, next_log - advance)
            elif old_data['delay'] >= read_period - 1:
                pause = self.min_pause
            pause = max(pause, self.min_pause)
            self.logger.debug(
                'delay %s, pause %g', str(old_data['delay']), pause)
            time.sleep(pause)
            # get new pointer
            last_ptr_time = ptr_time
            new_ptr = self.current_pos()
            ptr_time = time.time()
            # get new data
            last_data_time = data_time
            new_data = self.get_data(old_ptr, unbuffered=True)
            data_time = time.time()
            # when ptr changes, internal sensor data gets updated
            if new_ptr != old_ptr:
                for key in ('hum_in', 'temp_in', 'abs_pressure'):
                    old_data[key] = new_data[key]
            # log any change of status except 'invalid_wind_dir'
            new_status = decode_status(new_data['status'])
            last_status['invalid_wind_dir'] = new_status['invalid_wind_dir']
            if new_status != last_status:
                self.logger.warning('status %s', str(new_status))
            last_status = new_status
            if (new_status['lost_connection'] and not
                decode_status(old_data['status'])['lost_connection']):
                # 'lost connection' decision can happen at any time
                old_data = new_data
            # has data changed?
            if any(new_data[key] != old_data[key] for key in (
                    'hum_in', 'temp_in', 'hum_out', 'temp_out',
                    'abs_pressure', 'wind_ave', 'wind_gust', 'wind_dir',
                    'rain', 'status')):
                self.logger.debug('live_data new data')
                if data_time - last_data_time < self.margin:
                    # data has just changed, so definitely at a 48s update time
                    self._sensor_clock.set_clock(data_time)
                elif next_live and data_time < next_live - self.margin:
                    self.logger.warning(
                        'live_data lost sync %g', data_time - next_live)
                    self.logger.warning('old data %s', str(old_data))
                    self.logger.warning('new data %s', str(new_data))
                    self._sensor_clock.invalidate()
                next_live = self._sensor_clock.before(data_time + self.margin)
                if next_live:
                    if not logged_only:
                        result = dict(new_data)
                        result['idx'] = datetime.utcfromtimestamp(int(next_live))
                        yield result, old_ptr, False
                    next_live += live_interval
            elif next_live and data_time > next_live + 6.0:
                self.logger.info('live_data missed')
                next_live += live_interval
            old_data = new_data
            # has ptr changed?
            if new_ptr != old_ptr:
                self.logger.info('live_data new ptr: %06x', new_ptr)
                last_log = ptr_time - self.margin
                if ptr_time - last_ptr_time < self.margin:
                    # pointer has just changed, so definitely at a logging time
                    self._station_clock.set_clock(ptr_time)
                elif next_log:
                    if ptr_time < next_log - self.margin:
                        self.logger.warning(
                            'live_data lost log sync %g', ptr_time - next_log)
                        self._station_clock.invalidate()
                else:
                    self.logger.warning('missed ptr change time')
                if read_period > new_data['delay']:
                    read_period = new_data['delay']
                    self.logger.warning('reset read period %d', read_period)
                    log_interval = float(read_period * 60)
                next_log = self._station_clock.before(ptr_time + self.margin)
                if next_log:
                    result = dict(new_data)
                    result['idx'] = datetime.utcfromtimestamp(int(next_log))
                    yield result, old_ptr, True
                    next_log += log_interval
                old_ptr = new_ptr
                old_data['delay'] = 0
                data_time = 0
            elif ptr_time > last_log + log_interval + 180.0:
                # if station stops logging data, don't keep reading
                # USB until it locks up
                raise IOError('station is not logging data')
            elif next_log and ptr_time > next_log + 6.0:
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
        result = _decode(self.get_raw_data(ptr, unbuffered),
                         self._reading_format[self.ws_type])
        # split up 'wind_dir' byte
        if result['wind_dir'] is not None:
            result['status'] |= (result['wind_dir'] & 0xF0) << 4
            if result['wind_dir'] & 0x80:
                result['wind_dir'] = None
            else:
                result['wind_dir'] &= 0x0F
        return result

    def current_pos(self):
        """Get circular buffer location where current data is being written."""
        new_ptr = _decode(
            self._read_fixed_block(0x0020), self.lo_fix_format['current_pos'])
        if new_ptr == self._current_ptr:
            return self._current_ptr
        if self._current_ptr and new_ptr != self.inc_ptr(self._current_ptr):
            self.logger.error(
                'unexpected ptr change %06x -> %06x', self._current_ptr, new_ptr)
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
            pause = min(pause, self._station_clock.avoid())
            pause = min(pause, self._sensor_clock.avoid())
            if pause >= self.avoid * 2.0:
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
    _reading_format = {}
    _reading_format['1080'] = {
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
    _reading_format['3080'] = {
        'illuminance' : (16, 'u3', 0.1),
        'uv'          : (19, 'ub', None),
        }
    _reading_format['3080'].update(_reading_format['1080'])
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
        'magic_0'       : (0,  'pb', None),
        'magic_1'       : (1,  'pb', None),
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
