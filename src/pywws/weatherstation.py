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
are names of data items and the values can be an ``(offset, class,
kwds)`` tuple or another dictionary. So, for example, the
_reading_format dictionary entry ``'rain' : (13, WSFloat, {'signed':
False, 'scale': 0.3})`` means that the rain value is an unsigned short
(two bytes), 13 bytes from the start of the block, and should be
multiplied by 0.3 to get a useful value.

The use of nested dictionaries in the ``fixed_format`` dictionary
allows useful subsets of data to be decoded. For example, to decode
the entire block ``get_fixed_block`` is called with no parameters::

  ws = pywws.weatherstation.WeatherStation()
  print(ws.get_fixed_block())

To get the stored minimum external temperature, ``get_fixed_block`` is
called with a sequence of keys::

  ws = pywws.weatherstation.WeatherStation()
  print(ws.get_fixed_block(['min', 'temp_out', 'val']))

Often there is no requirement to read and decode the entire fixed
block, as its first 64 bytes contain the most useful data: the
interval between stored readings, the buffer address where the current
reading is stored, and the current date & time. The
``get_lo_fix_block`` method provides easy access to these.

For more examples of using the pywws.weatherstation module, see the
pywws.testweatherstation module.

Detailed API
------------

"""

from __future__ import absolute_import

__docformat__ = "restructuredtext en"

from ast import literal_eval
from datetime import datetime
import logging
import sys
import time

logger = logging.getLogger(__name__)


class WSBits(dict):
    @staticmethod
    def from_int(value, keys):
        # convert byte to list of 8 booleans
        mask = 1
        values = []
        for i in range(8):
            values.append(value & mask != 0)
            mask = mask << 1
        # merge with keys to make a dict
        return WSBits(zip(keys, values))

    @staticmethod
    def from_raw(raw, pos, keys=[]):
        return WSBits.from_int(raw[pos], keys)

    # don't display unknown bits
    def __repr__(self):
        result = {}
        for key in self:
            if self[key] or not key.startswith('bit'):
                result[key] = self[key]
        return repr(result)


class WSStatus(WSBits):
    keys = ('bit0', 'bit1', 'bit2', 'bit3', 'bit4', 'bit5',
            'lost_connection', 'rain_overflow')

    @classmethod
    def from_raw(cls, raw, pos):
        return WSStatus(WSBits.from_int(raw[pos], cls.keys))

    # convert to stringified int
    def to_csv(self):
        mask = 1
        value = 0
        for key in self.keys:
            if self[key]:
                value += mask
            mask = mask << 1
        return str(value)

    # convert from stringified int
    @classmethod
    def from_csv(cls, value):
        if not value:
            return None
        return WSStatus(WSBits.from_int(int(value), cls.keys))


class WSInt(int):
    @staticmethod
    def from_1(raw, pos, signed=False):
        # decode one byte to an int
        value = raw[pos]
        if value == 0xFF:
            return None
        if signed and value >= 0x80:
            value = 0x80 - value
        return WSInt(value)

    @staticmethod
    def wind_dir(raw, pos):
        # decode one byte to an int
        value = raw[pos]
        # if bit 7 is 1, value is invalid
        if value & 0x80:
            return None
        return WSInt(value)

    @staticmethod
    def from_2(raw, pos, signed=False):
        # decode two bytes to an int
        value = raw[pos] + (raw[pos+1] << 8)
        if value == 0xFFFF:
            return None
        if signed and value >= 0x8000:
            value = 0x8000 - value
        return WSInt(value)

    @staticmethod
    def from_3(raw, pos, signed=False):
        # decode three bytes to an int
        value = raw[pos] + (raw[pos+1] << 8) + (raw[pos+2] << 16)
        if value == 0xFFFFFF:
            return None
        if signed and value >= 0x800000:
            value = 0x800000 - value
        return WSInt(value)


def _nibble_value(raw, base_shift, nibble_pos=None, nibble_high=False):
    if nibble_pos is None:
        return 0
    mask = 0x0F
    shift = base_shift
    if nibble_high:
        mask = 0xF0
        shift = base_shift-4
    return ((raw[nibble_pos] & mask) << shift)


class WSFloat(float):
    @staticmethod
    def from_1(raw, pos, signed=False, scale=1.0, nibble_pos=None, nibble_high=False):
        # decode one byte to an int
        value = WSInt.from_1(raw, pos, signed=signed)
        if value is None:
            return None
        value += _nibble_value(raw, 8, nibble_pos=nibble_pos, nibble_high=nibble_high)
        # convert to float
        return WSFloat(float(value) * scale)

    @staticmethod
    def from_2(raw, pos, signed=False, scale=1.0, nibble_pos=None, nibble_high=False):
        # decode two bytes to an int
        value = WSInt.from_2(raw, pos, signed=signed)
        if value is None:
            return None
        value += _nibble_value(raw, 16, nibble_pos=nibble_pos, nibble_high=nibble_high)
        # convert to float
        return WSFloat(float(value) * scale)

    @staticmethod
    def from_3(raw, pos, signed=False, scale=1.0):
        # decode three bytes to an int
        value = WSInt.from_3(raw, pos, signed=signed)
        if value is None:
            return None
        # convert to float
        return WSFloat(float(value) * scale)

    # don't display excessive precision
    def __str__(self):
        return '{:.12g}'.format(self)

    def __repr__(self):
        return '{:.12g}'.format(self)


def _bcd_decode(byte):
    hi = (byte & 0xF0) >> 4
    lo = byte & 0x0F
    return (hi * 10) + lo


class WSTime(str):
    @staticmethod
    def from_raw(raw, pos):
        hour = _bcd_decode(raw[pos])
        minute = _bcd_decode(raw[pos+1])
        try:
            return WSTime('{:02d}:{:02d}'.format(hour, minute))
        except ValueError:
            return None


class WSDateTime(datetime):
    # only save string representation in 'fixed block' in status.ini
    def __repr__(self):
        return repr(self.strftime('%Y-%m-%d %H:%M:%S'))

    def to_csv(self):
        return self.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def from_csv(date_string):
        return WSDateTime(*map(int, (date_string[0:4],
                                     date_string[5:7],
                                     date_string[8:10],
                                     date_string[11:13],
                                     date_string[14:16],
                                     date_string[17:19])))

    @staticmethod
    def from_raw(raw, pos):
        year = _bcd_decode(raw[pos])
        month = _bcd_decode(raw[pos+1])
        day = _bcd_decode(raw[pos+2])
        hour = _bcd_decode(raw[pos+3])
        minute = _bcd_decode(raw[pos+4])
        try:
            return WSDateTime(year + 2000, month, day, hour, minute)
        except ValueError:
            return None


def _decode(raw, format_):
    if not raw:
        return None
    if isinstance(format_, dict):
        result = {}
        for key, value in format_.items():
            result[key] = _decode(raw, value)
    else:
        pos, factory, kwds = format_
        result = factory(raw, pos, **kwds)
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
        for module_name in ('device_libusb1', 'device_pyusb1', 'device_pyusb',
                            'device_ctypes_hidapi', 'device_cython_hidapi'):
            logger.debug('trying USB module %s', module_name)
            try:
                module = __import__(module_name, globals(), locals(), level=1)
                USBDevice = getattr(module, 'USBDevice')
                break
            except ImportError:
                pass
        else:
            raise ImportError('No USB library found')
        logger.info('using %s', module.__name__)
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
    def __init__(self, name, status, period, margin):
        self.name = name
        self.status = status
        self.period = period
        self.margin = margin
        if self.status:
            self.clock = literal_eval(
                self.status.get('clock', self.name, 'None'))
            self.drift = literal_eval(
                self.status.get('clock', self.name + ' drift', '0.0'))
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
            logger.error('unexpected %s clock change', self.name)
        self.clock = now
        logger.warning('setting %s clock %g', self.name, now % self.period)
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
            logger.warning(
                '%s clock drift %g %g', self.name, drift, self.drift)
            if self.status:
                self.status.set(
                    'clock', '%s drift' % self.name, str(self.drift))
        self.old_clock = self.clock

    def invalidate(self):
        self.clock = None


class WeatherStation(object):
    """Class that represents the weather station to user program."""
    # minimum interval between polling for data change
    min_pause = 0.5
    # margin of error for various decisions
    margin = (min_pause * 2.0) - 0.1

    def __init__(self, context=None):
        """Connect to weather station and prepare to read data."""
        # create basic IO object
        self.cusb = CUSBDrive()
        # init variables
        if context:
            self.status = context.status
            self.avoid = float(
                context.params.get('config', 'usb activity margin', '3.0'))
            self.avoid = max(self.avoid, 0.0)
            self.ws_type = context.params.get('config', 'ws type', 'Unknown')
        else:
            self.status = None
            self.avoid = 3.0
            self.ws_type = '1080'
        self._fixed_block = None
        self._data_block = None
        self._data_pos = None
        self._current_ptr = None
        self._station_clock = DriftingClock(
            'station', self.status, 60, self.avoid)
        self._sensor_clock = DriftingClock(
            'sensor', self.status, 48, self.avoid)
        if self.ws_type == '3080':
            self._solar_clock = DriftingClock(
                'solar', self.status, 60, self.avoid)
        else:
            self._solar_clock = None
        self.last_status = {}
        # check ws_type
        if self.ws_type not in ('1080', '3080'):
            if self.get_fixed_block(['lux_wm2_coeff']) == 0.0:
                guess = '1080'
            else:
                guess = '3080'
            raise ValueError("""
Unknown weather station type. Please edit weather.ini and set 'ws type' to
'1080' or '3080', as appropriate.
Your station is probably a '{:s}' type.
""".format(guess))

    def live_data(self, logged_only=False):
        # There are two things we want to synchronise to - the data is
        # updated every 48 seconds and the address is incremented
        # every 5 minutes (or 10, 15, ..., 30). Rather than getting
        # data every second or two, we sleep until one of the above is
        # due. (During initialisation we get data every half second
        # anyway.)
        read_period = self.get_fixed_block(['read_period'])
        logger.debug('read period %d', read_period)
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
        not_logging = False
        while True:
            # sleep until just before next reading is due
            now = time.time()
            advance = now + max(self.avoid, self.min_pause) + self.min_pause
            if next_live:
                pause = next_live - advance
            else:
                pause = self.min_pause
            if not_logging:
                pass
            elif next_log:
                pause = min(pause, next_log - advance)
            elif old_data['delay'] >= read_period - 1:
                pause = self.min_pause
            if (self._solar_clock and self._solar_clock.clock is None
                    and old_data['illuminance'] is not None):
                pause = self.min_pause
            pause = max(pause, self.min_pause)
            logger.debug(
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
            # log any change of status
            if new_data['status'] != self.last_status:
                logger.warning('status %s', str(new_data['status']))
            self.last_status = new_data['status']
            if (new_data['status']['lost_connection'] and not
                    old_data['status']['lost_connection']):
                # 'lost connection' decision can happen at any time
                old_data = new_data
            # has data changed?
            if any(new_data[key] != old_data[key] for key in (
                    'hum_in', 'temp_in', 'hum_out', 'temp_out',
                    'abs_pressure', 'wind_ave', 'wind_gust', 'wind_dir',
                    'rain', 'status')):
                logger.debug('live_data new data')
                if data_time - last_data_time < self.margin:
                    # data has just changed, so definitely at a 48s update time
                    self._sensor_clock.set_clock(data_time)
                elif next_live and data_time < next_live - self.margin:
                    logger.warning(
                        'live_data lost sync %g', data_time - next_live)
                    logger.warning('old data %s', str(old_data))
                    logger.warning('new data %s', str(new_data))
                    self._sensor_clock.invalidate()
                next_live = self._sensor_clock.before(data_time + self.margin)
                if next_live:
                    if not logged_only:
                        result = dict(new_data)
                        result['idx'] = datetime.utcfromtimestamp(int(next_live))
                        yield result, old_ptr, False
                    next_live += live_interval
                    if not_logging:
                        # simulate logging if station is not logging
                        if not next_log:
                            next_log = next_live
                        if next_live > next_log:
                            result = dict(new_data)
                            result['idx'] = datetime.utcfromtimestamp(int(next_log))
                            yield result, old_ptr, True
                            next_log += log_interval
            elif next_live and data_time > next_live + 6.0:
                logger.info('live_data missed')
                next_live += live_interval
            # has solar data changed?
            elif self._solar_clock and (
                    new_data['illuminance'] != old_data['illuminance'] or
                    new_data['uv'] != old_data['uv']):
                logger.debug('live_data new solar data')
                if data_time - last_data_time < self.margin:
                    # data has just changed, so at a solar update time
                    self._solar_clock.set_clock(data_time)
            old_data = new_data
            # has ptr changed?
            if new_ptr != old_ptr:
                logger.info('live_data new ptr: %06x', new_ptr)
                if not_logging:
                    logger.error('station is logging data')
                    not_logging = False
                last_log = ptr_time - self.margin
                if ptr_time - last_ptr_time < self.margin:
                    # pointer has just changed, so definitely at a logging time
                    self._station_clock.set_clock(ptr_time)
                elif next_log:
                    if ptr_time < next_log - self.margin:
                        logger.warning(
                            'live_data lost log sync %g', ptr_time - next_log)
                        self._station_clock.invalidate()
                else:
                    logger.info('missed ptr change time')
                if read_period > new_data['delay']:
                    read_period = new_data['delay']
                    logger.warning('reset read period %d', read_period)
                    log_interval = float(read_period * 60)
                result = dict(new_data)
                next_log = self._station_clock.before(ptr_time + self.margin)
                if next_log:
                    result['idx'] = datetime.utcfromtimestamp(int(next_log))
                    next_log += log_interval
                else:
                    # use best guess of logging time
                    result['idx'] = datetime.utcfromtimestamp(
                        int(ptr_time - (self.avoid / 2)))
                yield result, old_ptr, True
                old_ptr = new_ptr
                old_data['delay'] = 0
                data_time = 0
            elif ptr_time > last_log + log_interval + 180.0:
                # if station stops logging data, don't keep reading
                # USB until it locks up
                logger.error('station is not logging data')
                not_logging = True
            elif next_log and ptr_time > next_log + 6.0:
                logger.warning('live_data log extended')
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
        return result

    def current_pos(self):
        """Get circular buffer location where current data is being written."""
        new_ptr = _decode(
            self._read_fixed_block(0x0020), self.lo_fix_format['current_pos'])
        if new_ptr == self._current_ptr:
            return self._current_ptr
        if self._current_ptr and new_ptr != self.inc_ptr(self._current_ptr):
            logger.error(
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
            pause = min(self._station_clock.avoid(), self._sensor_clock.avoid())
            if self._solar_clock:
                pause = min(pause, self._solar_clock.avoid())
            if pause >= self.avoid * 2.0:
                return
            logger.debug('avoid %s', str(pause))
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
                    logger.debug('_read_block changing %06x', ptr)
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
            logger.debug('write_data waiting for ack')
            time.sleep(6)

    # Tables of "meanings" for raw weather station data. Each key
    # specifies an (offset, factory, kwds) tuple that is understood
    # by _decode.
    # depends on weather station type
    _reading_format = {}
    _reading_format['1080'] = {
        'delay'        : (0, WSInt.from_1, {'signed': False}),
        'hum_in'       : (1, WSInt.from_1, {'signed': False}),
        'temp_in'      : (2, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
        'hum_out'      : (4, WSInt.from_1, {'signed': False}),
        'temp_out'     : (5, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
        'abs_pressure' : (7, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
        'wind_ave'     : (9, WSFloat.from_1, {'scale': 0.1, 'nibble_pos':11, 'nibble_high':False}),
        'wind_gust'    : (10, WSFloat.from_1, {'scale': 0.1, 'nibble_pos':11, 'nibble_high':True}),
        'wind_dir'     : (12, WSInt.wind_dir, {}),
        'rain'         : (13, WSFloat.from_2, {'signed': False, 'scale': 0.3}),
        'status'       : (15, WSStatus.from_raw, {}),
        }
    _reading_format['3080'] = {
        'illuminance' : (16, WSFloat.from_3, {'signed': False, 'scale': 0.1}),
        'uv'          : (19, WSInt.from_1, {'signed': False}),
        }
    _reading_format['3080'].update(_reading_format['1080'])
    lo_fix_format = {
        'read_period'   : (16, WSInt.from_1, {'signed': False}),
        'settings_1'    : (17, WSBits.from_raw, {'keys': (
            'temp_in_F', 'temp_out_F', 'rain_in', 'bit3', 'bit4',
            'pressure_hPa', 'pressure_inHg', 'pressure_mmHg')}),
        'settings_2'    : (18, WSBits.from_raw, {'keys': (
            'wind_mps', 'wind_kmph', 'wind_knot', 'wind_mph', 'wind_bft',
            'bit5', 'bit6', 'bit7')}),
        'display_1'     : (19, WSBits.from_raw, {'keys': (
            'pressure_rel', 'wind_gust', 'clock_12hr', 'date_mdy',
            'time_scale_24', 'show_year', 'show_day_name', 'alarm_time')}),
        'display_2'     : (20, WSBits.from_raw, {'keys': (
            'temp_out_temp', 'temp_out_chill', 'temp_out_dew', 'rain_hour',
            'rain_day', 'rain_week', 'rain_month', 'rain_total')}),
        'alarm_1'       : (21, WSBits.from_raw, {'keys': (
            'bit0', 'time', 'wind_dir', 'bit3', 'hum_in_lo', 'hum_in_hi',
            'hum_out_lo', 'hum_out_hi')}),
        'alarm_2'       : (22, WSBits.from_raw, {'keys': (
            'wind_ave', 'wind_gust', 'rain_hour', 'rain_day',
            'pressure_abs_lo', 'pressure_abs_hi',
            'pressure_rel_lo', 'pressure_rel_hi')}),
        'alarm_3'       : (23, WSBits.from_raw, {'keys': (
            'temp_in_lo', 'temp_in_hi', 'temp_out_lo', 'temp_out_hi',
            'wind_chill_lo', 'wind_chill_hi', 'dew_point_lo', 'dew_point_hi')}),
        'timezone'      : (24, WSInt.from_1, {'signed': True}),
        'unknown_01'    : (25, WSInt.from_1, {'signed': False}),
        'data_changed'  : (26, WSInt.from_1, {'signed': False}),
        'data_count'    : (27, WSInt.from_2, {'signed': False}),
        'display_3'     : (29, WSBits.from_raw, {'keys': (
            'illuminance_fc', 'alarm_illuminance_hi', 'alarm_uv_hi', 'bit3', 'bit4', 'illuminance_wm2', 'bit6',
            'bit7')}),
        'current_pos'   : (30, WSInt.from_2, {'signed': False}),
        }
    fixed_format = {
        'magic_0'       : (0,  WSInt.from_1, {'signed': False}),
        'magic_1'       : (1,  WSInt.from_1, {'signed': False}),
        'rain_factor_raw': (2,  WSFloat.from_2, {'signed': False}),
        'wind_factor_raw': (4,  WSFloat.from_2, {'signed': False}),
        'rel_pressure'  : (32, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
        'abs_pressure'  : (34, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
        'lux_wm2_coeff' : (36, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
        'date_time'     : (43, WSDateTime.from_raw, {}),
        'unknown_18'    : (97, WSInt.from_1, {'signed': False}),
        'alarm'         : {
            'hum_in'        : {'hi' : (48, WSInt.from_1, {'signed': False}),
                               'lo' : (49, WSInt.from_1, {'signed': False})},
            'temp_in'       : {'hi' : (50, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'lo' : (52, WSFloat.from_2, {'signed': True, 'scale': 0.1})},
            'hum_out'       : {'hi' : (54, WSInt.from_1, {'signed': False}),
                               'lo' : (55, WSInt.from_1, {'signed': False})},
            'temp_out'      : {'hi' : (56, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'lo' : (58, WSFloat.from_2, {'signed': True, 'scale': 0.1})},
            'windchill'     : {'hi' : (60, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'lo' : (62, WSFloat.from_2, {'signed': True, 'scale': 0.1})},
            'dewpoint'      : {'hi' : (64, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'lo' : (66, WSFloat.from_2, {'signed': True, 'scale': 0.1})},
            'abs_pressure'  : {'hi' : (68, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
                               'lo' : (70, WSFloat.from_2, {'signed': False, 'scale': 0.1})},
            'rel_pressure'  : {'hi' : (72, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
                               'lo' : (74, WSFloat.from_2, {'signed': False, 'scale': 0.1})},
            'wind_ave'      : {'bft': (76, WSInt.from_1, {'signed': False}),
                               'ms' : (77, WSFloat.from_1, {'signed': False, 'scale': 0.1})},
            'wind_gust'     : {'bft': (79, WSInt.from_1, {'signed': False}),
                               'ms' : (80, WSFloat.from_1, {'signed': False, 'scale': 0.1})},
            'wind_dir'      : (82, WSInt.wind_dir, {}),
            'rain'          : {'hour' : (83, WSFloat.from_2, {'signed': False, 'scale': 0.3}),
                               'day'  : (85, WSFloat.from_2, {'signed': False, 'scale': 0.3})},
            'time'          : (87, WSTime.from_raw, {}),
            'illuminance'   : (89, WSFloat.from_3, {'signed': False, 'scale': 0.1}),
            'uv'            : (92, WSInt.from_1, {'signed': False}),
            },
        'max'           : {
            'uv'            : {'val' : (93, WSInt.from_1, {'signed': False}),
                               'date': (6, WSDateTime.from_raw, {})},
            'illuminance'   : {'val' : (94, WSFloat.from_3, {'signed': False, 'scale': 0.1}),
                               'date': (11, WSDateTime.from_raw, {})},
            'hum_in'        : {'val' : (98, WSInt.from_1, {'signed': False}),
                               'date': (141, WSDateTime.from_raw, {})},
            'hum_out'       : {'val' : (100, WSInt.from_1, {'signed': False}),
                               'date': (151, WSDateTime.from_raw, {})},
            'temp_in'       : {'val' : (102, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'date': (161, WSDateTime.from_raw, {})},
            'temp_out'      : {'val' : (106, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'date': (171, WSDateTime.from_raw, {})},
            'windchill'     : {'val' : (110, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'date': (181, WSDateTime.from_raw, {})},
            'dewpoint'      : {'val' : (114, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'date': (191, WSDateTime.from_raw, {})},
            'abs_pressure'  : {'val' : (118, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
                               'date': (201, WSDateTime.from_raw, {})},
            'rel_pressure'  : {'val' : (122, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
                               'date': (211, WSDateTime.from_raw, {})},
            'wind_ave'      : {'val' : (126, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
                               'date': (221, WSDateTime.from_raw, {})},
            'wind_gust'     : {'val' : (128, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
                               'date': (226, WSDateTime.from_raw, {})},
            'rain'          : {
                'hour'          : {'val' : (130, WSFloat.from_2, {'signed': False, 'scale': 0.3}),
                                   'date': (231, WSDateTime.from_raw, {})},
                'day'           : {'val' : (132, WSFloat.from_2, {'signed': False, 'scale': 0.3}),
                                   'date': (236, WSDateTime.from_raw, {})},
                'week'          : {'val' : (134, WSFloat.from_2, {'signed': False, 'scale': 0.3}),
                                   'date': (241, WSDateTime.from_raw, {})},
                'month'         : {'val' : (136, WSFloat.from_2, {'signed': False, 'scale': 0.3, 'nibble_pos':140, 'nibble_high':True}),
                                   'date': (246, WSDateTime.from_raw, {})},
                'total'         : {'val' : (138, WSFloat.from_2, {'signed': False, 'scale': 0.3, 'nibble_pos':140, 'nibble_high':False}),
                                   'date': (251, WSDateTime.from_raw, {})},
                },
            },
        'min'           : {
            'hum_in'        : {'val' : (99, WSInt.from_1, {'signed': False}),
                               'date': (146, WSDateTime.from_raw, {})},
            'hum_out'       : {'val' : (101, WSInt.from_1, {'signed': False}),
                               'date': (156, WSDateTime.from_raw, {})},
            'temp_in'       : {'val' : (104, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'date': (166, WSDateTime.from_raw, {})},
            'temp_out'      : {'val' : (108, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'date': (176, WSDateTime.from_raw, {})},
            'windchill'     : {'val' : (112, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'date': (186, WSDateTime.from_raw, {})},
            'dewpoint'      : {'val' : (116, WSFloat.from_2, {'signed': True, 'scale': 0.1}),
                               'date': (196, WSDateTime.from_raw, {})},
            'abs_pressure'  : {'val' : (120, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
                               'date': (206, WSDateTime.from_raw, {})},
            'rel_pressure'  : {'val' : (124, WSFloat.from_2, {'signed': False, 'scale': 0.1}),
                               'date': (216, WSDateTime.from_raw, {})},
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
