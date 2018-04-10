# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-18  pywws contributors

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

"""Store parameters and weather data in easy to access files

Introduction
------------

This module is at the core of pywws. It stores data on disc, but without
the overhead of a full scale database system. I have designed it to run
on a small memory machine such as a Raspberry Pi or even a router. To
minimise memory usage it only loads one day's worth of raw data at a
time into memory.

From a "user" point of view, the data is accessed as a cross between a
list and a dictionary. Each data record is indexed by a
:py:class:`datetime.datetime` object (dictionary behaviour), but
records are stored in order and can be accessed as slices (list
behaviour).

For example, to access the hourly data for Christmas day 2009, one
might do the following::

  from datetime import datetime
  import pywws.storage
  hourly = pywws.storage.HourlyStore('weather_data')
  for data in hourly[datetime(2009, 12, 25):datetime(2009, 12, 26)]:
      print(data['idx'], data['temp_out'])

Some more examples of data access::

  # get value nearest 9:30 on Christmas day 2008
  data[data.nearest(datetime(2008, 12, 25, 9, 30))]
  # get entire array, equivalent to data[:]
  data[datetime.min:datetime.max]
  # get last 12 hours worth of data
  data[datetime.utcnow() - timedelta(hours=12):]

Note that the :py:class:`datetime.datetime` index is in UTC. You may
need to apply an offset to convert to local time.

The module provides five classes to store different data.
:py:class:`RawStore` takes "raw" data from the weather station;
:py:class:`CalibStore`, :py:class:`HourlyStore`, :py:class:`DailyStore`
and :py:class:`MonthlyStore` store processed data (see
:py:mod:`pywws.process`). All are derived from the same ``CoreStore``
class, they only differ in the keys and types of data stored in each
record.

Detailed API
------------

"""

from __future__ import with_statement

from contextlib import contextmanager
import csv
from datetime import date, datetime, timedelta, MAXYEAR
import os
import sys
import threading
import time

if sys.version_info[0] >= 3:
    from configparser import RawConfigParser
else:
    from ConfigParser import RawConfigParser

from pywws.constants import DAY
from pywws.weatherstation import WSDateTime, WSFloat, WSInt, WSStatus


class ParamStore(object):
    def __init__(self, root_dir, file_name):
        self._lock = threading.Lock()
        with self._lock:
            if not os.path.isdir(root_dir):
                raise RuntimeError(
                    'Directory "' + root_dir + '" does not exist.')
            self._path = os.path.join(root_dir, file_name)
            self._dirty = False
            # open config file
            self._config = RawConfigParser()
            self._config.read(self._path)

    def flush(self):
        if not self._dirty:
            return
        with self._lock:
            self._dirty = False
            with open(self._path, 'w') as of:
                self._config.write(of)

    def get(self, section, option, default=None):
        """Get a parameter value and return a string.

        If default is specified and section or option are not defined
        in the file, they are created and set to default, which is
        then the return value.

        """
        with self._lock:
            if not self._config.has_option(section, option):
                if default is not None:
                    self._set(section, option, default)
                return default
            return self._config.get(section, option)

    def get_datetime(self, section, option, default=None):
        result = self.get(section, option, default)
        if result:
            return WSDateTime.from_csv(result)
        return result

    def set(self, section, option, value):
        """Set option in section to string value."""
        with self._lock:
            self._set(section, option, value)

    def _set(self, section, option, value):
        if not self._config.has_section(section):
            self._config.add_section(section)
        elif (self._config.has_option(section, option) and
              self._config.get(section, option) == value):
            return
        self._config.set(section, option, value)
        self._dirty = True

    def unset(self, section, option):
        """Remove option from section."""
        with self._lock:
            if not self._config.has_section(section):
                return
            if self._config.has_option(section, option):
                self._config.remove_option(section, option)
                self._dirty = True
            if not self._config.options(section):
                self._config.remove_section(section)
                self._dirty = True


class _Cache(object):
    def __init__(self):
        self.data = []
        self.ptr = 0
        self.path = ''
        self.lo = date.max
        self.hi = date.min
        self.dirty = False

    def copy(self, other):
        self.data = other.data
        self.ptr = other.ptr
        self.path = other.path
        self.lo = other.lo
        self.hi = other.hi
        self.dirty = False

    def set_ptr(self, idx):
        hi = len(self.data) - 1
        if hi < 0 or self.data[0]['idx'] >= idx:
            self.ptr = 0
            return
        if self.data[hi]['idx'] < idx:
            self.ptr = hi + 1
            return
        lo = 0
        start = min(self.ptr, hi)
        if self.data[start]['idx'] < idx:
            lo = start
        else:
            hi = start
        while hi > lo + 1:
            mid = (lo + hi) // 2
            if self.data[mid]['idx'] < idx:
                lo = mid
            else:
                hi = mid
        self.ptr = hi


class CoreStore(object):
    def __init__(self, root_dir):
        self._root_dir = os.path.join(root_dir, self.dir_name)
        if not os.path.isdir(self._root_dir):
            os.mkdir(self._root_dir)
        # initialise caches
        self._wr_cache = _Cache()
        self._rd_cache = _Cache()
        # get conservative first and last days for which data (might) exist
        self._lo_limit = date.max - timedelta(days=500)
        self._hi_limit = date.min + timedelta(days=500)
        for root, dirs, files in os.walk(self._root_dir):
            files.sort()
            for file in files:
                if file[0] == '.':
                    continue
                path, self._lo_limit, hi = self._get_cache_path(
                    datetime.strptime(file, "%Y-%m-%d.txt").date())
                break
            else:
                dirs.sort()
                continue
            break
        for root, dirs, files in os.walk(self._root_dir):
            files.sort()
            files.reverse()
            for file in files:
                if file[0] == '.':
                    continue
                path, lo, self._hi_limit = self._get_cache_path(
                    datetime.strptime(file, "%Y-%m-%d.txt").date())
                break
            else:
                dirs.sort()
                dirs.reverse()
                continue
            break
        self._lo_limit_dt = datetime(
            self._lo_limit.year, self._lo_limit.month, self._lo_limit.day)
        self._hi_limit_dt = datetime(
            self._hi_limit.year, self._hi_limit.month, self._hi_limit.day)

    def _slice(self, i):
        if i.step is not None:
            raise TypeError("slice step not permitted")
        a = i.start
        if a is None:
            a = self._lo_limit_dt
        elif not isinstance(a, datetime):
            raise TypeError("slice indices must be %s or None" % (datetime))
        elif a < self._lo_limit_dt:
            a = self._lo_limit_dt
        b = i.stop
        if b is None:
            b = self._hi_limit_dt
        elif not isinstance(b, datetime):
            raise TypeError("slice indices must be %s or None" % (datetime))
        elif b > self._hi_limit_dt:
            b = self._hi_limit_dt
        return a, b

    def _get_slice(self, i):
        a, b = self._slice(i)
        if a > b:
            return
        # go to start of slice
        self._set_cache_ptr(self._rd_cache, a)
        cache = self._rd_cache.data
        cache_hi = self._rd_cache.hi
        cache_ptr = self._rd_cache.ptr
        # iterate over complete caches
        while cache_hi <= b.date():
            for data in cache[cache_ptr:]:
                yield data
            if cache_hi >= self._hi_limit:
                return
            self._load(self._rd_cache, cache_hi)
            cache = self._rd_cache.data
            cache_hi = self._rd_cache.hi
            cache_ptr = 0
        # iterate over part of cache
        for data in cache[cache_ptr:]:
            if data['idx'] >= b:
                return
            yield data

    def __getitem__(self, i):
        """Return the data item or items with index i.

        i must be a datetime object or a slice.
        If i is a single datetime then a value with that index must exist."""
        if isinstance(i, slice):
            return self._get_slice(i)
        if not isinstance(i, datetime):
            raise TypeError("list indices must be %s" % (datetime))
        self._set_cache_ptr(self._rd_cache, i)
        if (self._rd_cache.ptr >= len(self._rd_cache.data) or
            self._rd_cache.data[self._rd_cache.ptr]['idx'] != i):
            raise KeyError(i)
        return self._rd_cache.data[self._rd_cache.ptr]

    def __setitem__(self, i, x):
        """Store a value x with index i.

        i must be a datetime object.
        If there is already a value with index i, it is overwritten.
        """
        if not isinstance(i, datetime):
            raise TypeError("index '%s' is not %s" % (i, datetime))
        x['idx'] = i
        self._set_cache_ptr(self._wr_cache, i)
        if len(self._wr_cache.data) == 0:
            self._lo_limit = min(self._lo_limit, self._wr_cache.lo)
            self._hi_limit = max(self._hi_limit, self._wr_cache.hi)
            self._lo_limit_dt = datetime(
                self._lo_limit.year, self._lo_limit.month, self._lo_limit.day)
            self._hi_limit_dt = datetime(
                self._hi_limit.year, self._hi_limit.month, self._hi_limit.day)
        if (self._wr_cache.ptr < len(self._wr_cache.data) and
            self._wr_cache.data[self._wr_cache.ptr]['idx'] == i):
            self._wr_cache.data[self._wr_cache.ptr] = x
        else:
            self._wr_cache.data.insert(self._wr_cache.ptr, x)
        self._wr_cache.dirty = True

    def _del_slice(self, i):
        a, b = self._slice(i)
        if a > b:
            return
        # go to start of slice
        self._set_cache_ptr(self._wr_cache, a)
        # delete to end of cache
        while self._wr_cache.hi <= b.date():
            del self._wr_cache.data[self._wr_cache.ptr:]
            self._wr_cache.dirty = True
            if self._wr_cache.hi >= self._hi_limit:
                return
            self._load(self._wr_cache, self._wr_cache.hi)
            self._wr_cache.ptr = 0
        # delete part of cache
        ptr = self._wr_cache.ptr
        self._wr_cache.set_ptr(b)
        del self._wr_cache.data[ptr:self._wr_cache.ptr]
        self._wr_cache.dirty = True

    def __delitem__(self, i):
        """Delete the data item or items with index i.

        i must be a datetime object or a slice.
        If i is a single datetime then a value with that index must exist."""
        if isinstance(i, slice):
            return self._del_slice(i)
        if not isinstance(i, datetime):
            raise TypeError("list indices must be %s" % (datetime))
        self._set_cache_ptr(self._wr_cache, i)
        if (self._wr_cache.ptr >= len(self._wr_cache.data) or
            self._wr_cache.data[self._wr_cache.ptr]['idx'] != i):
            raise KeyError(i)
        del self._wr_cache.data[self._wr_cache.ptr]
        self._wr_cache.dirty = True

    def before(self, idx):
        """Return datetime of newest existing data record whose
        datetime is < idx.

        Might not even be in the same year! If no such record exists,
        return None."""
        if not isinstance(idx, datetime):
            raise TypeError("'%s' is not %s" % (idx, datetime))
        day = min(idx.date(), self._hi_limit - DAY)
        while day >= self._lo_limit:
            if day < self._rd_cache.lo or day >= self._rd_cache.hi:
                self._load(self._rd_cache, day)
            self._rd_cache.set_ptr(idx)
            if self._rd_cache.ptr > 0:
                return self._rd_cache.data[self._rd_cache.ptr - 1]['idx']
            day = self._rd_cache.lo - DAY
        return None

    def after(self, idx):
        """Return datetime of oldest existing data record whose
        datetime is >= idx.

        Might not even be in the same year! If no such record exists,
        return None."""
        if not isinstance(idx, datetime):
            raise TypeError("'%s' is not %s" % (idx, datetime))
        day = max(idx.date(), self._lo_limit)
        while day < self._hi_limit:
            if day < self._rd_cache.lo or day >= self._rd_cache.hi:
                self._load(self._rd_cache, day)
            self._rd_cache.set_ptr(idx)
            if self._rd_cache.ptr < len(self._rd_cache.data):
                return self._rd_cache.data[self._rd_cache.ptr]['idx']
            day = self._rd_cache.hi
        return None

    def nearest(self, idx):
        """Return datetime of record whose datetime is nearest idx."""
        hi = self.after(idx)
        lo = self.before(idx)
        if hi is None:
            return lo
        if lo is None:
            return hi
        if abs(hi - idx) < abs(lo - idx):
            return hi
        return lo

    def _set_cache_ptr(self, cache, i):
        day = i.date()
        if day < cache.lo or day >= cache.hi:
            self._load(cache, day)
        cache.set_ptr(i)

    def _load(self, cache, target_date):
        self._flush(cache)
        new_path, new_lo, new_hi = self._get_cache_path(target_date)
        if new_path == self._wr_cache.path:
            cache.copy(self._wr_cache)
            return
        if new_path == self._rd_cache.path:
            cache.copy(self._rd_cache)
            return
        cache.data = []
        cache.ptr = 0
        cache.path, cache.lo, cache.hi = new_path, new_lo, new_hi
        if not os.path.exists(cache.path):
            return
        if sys.version_info[0] >= 3:
            kwds = {'mode': 'r', 'newline': ''}
        else:
            kwds = {'mode': 'rb'}
        with open(cache.path, **kwds) as csvfile:
            reader = csv.reader(csvfile, quoting=csv.QUOTE_NONE)
            for row in reader:
                result = {}
                for key, value in zip(self.key_list, row):
                    if value == '':
                        result[key] = None
                    else:
                        result[key] = self.conv[key](value)
                cache.data.append(result)

    def flush(self):
        self._flush(self._wr_cache)
        self._flush(self._rd_cache)

    def _flush(self, cache):
        if not cache.dirty:
            return
        cache.dirty = False
        if len(cache.data) == 0:
            if os.path.exists(cache.path):
                # existing data has been wiped, so delete file
                os.unlink(cache.path)
            return
        dir = os.path.dirname(cache.path)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        if sys.version_info[0] >= 3:
            kwds = {'mode': 'w', 'newline': ''}
        else:
            kwds = {'mode': 'wb'}
        conv = {
            datetime  : str,
            float     : lambda x: '{:.12g}'.format(x),
            int       : str,
            type(None): lambda x: '',
            WSDateTime: WSDateTime.to_csv,
            WSFloat   : str,
            WSInt     : str,
            WSStatus  : WSStatus.to_csv,
            }
        with open(cache.path, **kwds) as csvfile:
            for data in cache.data:
                row = []
                for key in self.key_list[:len(data)]:
                    value = data[key]
                    row.append(conv[type(value)](value))
                csvfile.write(','.join(row) + '\n')

    def _get_cache_path(self, target_date):
        # default implementation - one file per day
        path = os.path.join(self._root_dir,
                            target_date.strftime("%Y"),
                            target_date.strftime("%Y-%m"),
                            target_date.strftime("%Y-%m-%d.txt"))
        lo = min(target_date, date.max - DAY)
        hi = lo + DAY
        return path, lo, hi


class RawStore(CoreStore):
    """Stores raw weather station data."""
    dir_name = 'raw'
    key_list = [
        'idx', 'delay', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
        'abs_pressure', 'wind_ave', 'wind_gust', 'wind_dir', 'rain',
        'status', 'illuminance', 'uv',
        ]
    conv = {
        'idx'          : WSDateTime.from_csv,
        'delay'        : int,
        'hum_in'       : int,
        'temp_in'      : float,
        'hum_out'      : int,
        'temp_out'     : float,
        'abs_pressure' : float,
        'wind_ave'     : float,
        'wind_gust'    : float,
        'wind_dir'     : int,
        'rain'         : float,
        'status'       : WSStatus.from_csv,
        'illuminance'  : float,
        'uv'           : int,
        }


class CalibStore(CoreStore):
    """Stores 'calibrated' weather station data."""
    dir_name = 'calib'
    key_list = [
        'idx', 'delay', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
        'abs_pressure', 'rel_pressure', 'wind_ave', 'wind_gust', 'wind_dir',
        'rain', 'status', 'illuminance', 'uv',
        ]
    conv = {
        'idx'          : WSDateTime.from_csv,
        'delay'        : int,
        'hum_in'       : int,
        'temp_in'      : float,
        'hum_out'      : int,
        'temp_out'     : float,
        'abs_pressure' : float,
        'rel_pressure' : float,
        'wind_ave'     : float,
        'wind_gust'    : float,
        'wind_dir'     : float,
        'rain'         : float,
        'status'       : WSStatus.from_csv,
        'illuminance'  : float,
        'uv'           : int,
        }


class HourlyStore(CoreStore):
    """Stores hourly summary weather station data."""
    dir_name = 'hourly'
    key_list = [
        'idx', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
        'abs_pressure', 'rel_pressure', 'pressure_trend',
        'wind_ave', 'wind_gust', 'wind_dir', 'rain', 'illuminance', 'uv',
        ]
    conv = {
        'idx'               : WSDateTime.from_csv,
        'hum_in'            : int,
        'temp_in'           : float,
        'hum_out'           : int,
        'temp_out'          : float,
        'abs_pressure'      : float,
        'rel_pressure'      : float,
        'pressure_trend'    : float,
        'wind_ave'          : float,
        'wind_gust'         : float,
        'wind_dir'          : float,
        'rain'              : float,
        'illuminance'       : float,
        'uv'                : int,
        }


class DailyStore(CoreStore):
    """Stores daily summary weather station data."""
    dir_name = 'daily'
    key_list = [
        'idx', 'start',
        'hum_out_ave',
        'hum_out_min', 'hum_out_min_t', 'hum_out_max', 'hum_out_max_t',
        'temp_out_ave',
        'temp_out_min', 'temp_out_min_t', 'temp_out_max', 'temp_out_max_t',
        'hum_in_ave',
        'hum_in_min', 'hum_in_min_t', 'hum_in_max', 'hum_in_max_t',
        'temp_in_ave',
        'temp_in_min', 'temp_in_min_t', 'temp_in_max', 'temp_in_max_t',
        'abs_pressure_ave',
        'abs_pressure_min', 'abs_pressure_min_t',
        'abs_pressure_max', 'abs_pressure_max_t',
        'rel_pressure_ave',
        'rel_pressure_min', 'rel_pressure_min_t',
        'rel_pressure_max', 'rel_pressure_max_t',
        'wind_ave', 'wind_gust', 'wind_gust_t', 'wind_dir',
        'rain',
        'illuminance_ave', 'illuminance_max', 'illuminance_max_t',
        'uv_ave', 'uv_max', 'uv_max_t',
        ]
    conv = {
        'idx'                : WSDateTime.from_csv,
        'start'              : WSDateTime.from_csv,
        'hum_out_ave'        : float,
        'hum_out_min'        : int,
        'hum_out_min_t'      : WSDateTime.from_csv,
        'hum_out_max'        : int,
        'hum_out_max_t'      : WSDateTime.from_csv,
        'temp_out_ave'       : float,
        'temp_out_min'       : float,
        'temp_out_min_t'     : WSDateTime.from_csv,
        'temp_out_max'       : float,
        'temp_out_max_t'     : WSDateTime.from_csv,
        'hum_in_ave'         : float,
        'hum_in_min'         : int,
        'hum_in_min_t'       : WSDateTime.from_csv,
        'hum_in_max'         : int,
        'hum_in_max_t'       : WSDateTime.from_csv,
        'temp_in_ave'        : float,
        'temp_in_min'        : float,
        'temp_in_min_t'      : WSDateTime.from_csv,
        'temp_in_max'        : float,
        'temp_in_max_t'      : WSDateTime.from_csv,
        'abs_pressure_ave'   : float,
        'abs_pressure_min'   : float,
        'abs_pressure_min_t' : WSDateTime.from_csv,
        'abs_pressure_max'   : float,
        'abs_pressure_max_t' : WSDateTime.from_csv,
        'rel_pressure_ave'   : float,
        'rel_pressure_min'   : float,
        'rel_pressure_min_t' : WSDateTime.from_csv,
        'rel_pressure_max'   : float,
        'rel_pressure_max_t' : WSDateTime.from_csv,
        'wind_ave'           : float,
        'wind_gust'          : float,
        'wind_gust_t'        : WSDateTime.from_csv,
        'wind_dir'           : float,
        'rain'               : float,
        'illuminance_ave'    : float,
        'illuminance_max'    : float,
        'illuminance_max_t'  : WSDateTime.from_csv,
        'uv_ave'             : float,
        'uv_max'             : int,
        'uv_max_t'           : WSDateTime.from_csv,
        }

    def _get_cache_path(self, target_date):
        # one file per month
        path = os.path.join(self._root_dir,
                            target_date.strftime("%Y"),
                            target_date.strftime("%Y-%m-01.txt"))
        lo = target_date.replace(day=1)
        if lo.month < 12:
            hi = lo.replace(month=lo.month+1)
        elif lo.year < MAXYEAR:
            hi = lo.replace(year=lo.year+1, month=1)
        else:
            hi = lo
            lo = hi.replace(month=hi.month-1)
        return path, lo, hi


class MonthlyStore(CoreStore):
    """Stores monthly summary weather station data."""
    dir_name = 'monthly'
    key_list = [
        'idx', 'start',
        'hum_out_ave',
        'hum_out_min', 'hum_out_min_t', 'hum_out_max', 'hum_out_max_t',
        'temp_out_ave',
        'temp_out_min_lo', 'temp_out_min_lo_t',
        'temp_out_min_hi', 'temp_out_min_hi_t', 'temp_out_min_ave',
        'temp_out_max_lo', 'temp_out_max_lo_t',
        'temp_out_max_hi', 'temp_out_max_hi_t', 'temp_out_max_ave',
        'hum_in_ave',
        'hum_in_min', 'hum_in_min_t', 'hum_in_max', 'hum_in_max_t',
        'temp_in_ave',
        'temp_in_min_lo', 'temp_in_min_lo_t',
        'temp_in_min_hi', 'temp_in_min_hi_t', 'temp_in_min_ave',
        'temp_in_max_lo', 'temp_in_max_lo_t',
        'temp_in_max_hi', 'temp_in_max_hi_t', 'temp_in_max_ave',
        'abs_pressure_ave',
        'abs_pressure_min', 'abs_pressure_min_t',
        'abs_pressure_max', 'abs_pressure_max_t',
        'rel_pressure_ave',
        'rel_pressure_min', 'rel_pressure_min_t',
        'rel_pressure_max', 'rel_pressure_max_t',
        'wind_ave', 'wind_gust', 'wind_gust_t', 'wind_dir',
        'rain', 'rain_days',
        'illuminance_ave',
        'illuminance_max_lo', 'illuminance_max_lo_t',
        'illuminance_max_hi', 'illuminance_max_hi_t', 'illuminance_max_ave',
        'uv_ave',
        'uv_max_lo', 'uv_max_lo_t', 'uv_max_hi', 'uv_max_hi_t', 'uv_max_ave',
        ]
    conv = {
        'idx'                  : WSDateTime.from_csv,
        'start'                : WSDateTime.from_csv,
        'hum_out_ave'          : float,
        'hum_out_min'          : int,
        'hum_out_min_t'        : WSDateTime.from_csv,
        'hum_out_max'          : int,
        'hum_out_max_t'        : WSDateTime.from_csv,
        'temp_out_ave'         : float,
        'temp_out_min_lo'      : float,
        'temp_out_min_lo_t'    : WSDateTime.from_csv,
        'temp_out_min_hi'      : float,
        'temp_out_min_hi_t'    : WSDateTime.from_csv,
        'temp_out_min_ave'     : float,
        'temp_out_max_lo'      : float,
        'temp_out_max_lo_t'    : WSDateTime.from_csv,
        'temp_out_max_hi'      : float,
        'temp_out_max_hi_t'    : WSDateTime.from_csv,
        'temp_out_max_ave'     : float,
        'hum_in_ave'           : float,
        'hum_in_min'           : int,
        'hum_in_min_t'         : WSDateTime.from_csv,
        'hum_in_max'           : int,
        'hum_in_max_t'         : WSDateTime.from_csv,
        'temp_in_ave'          : float,
        'temp_in_min_lo'       : float,
        'temp_in_min_lo_t'     : WSDateTime.from_csv,
        'temp_in_min_hi'       : float,
        'temp_in_min_hi_t'     : WSDateTime.from_csv,
        'temp_in_min_ave'      : float,
        'temp_in_max_lo'       : float,
        'temp_in_max_lo_t'     : WSDateTime.from_csv,
        'temp_in_max_hi'       : float,
        'temp_in_max_hi_t'     : WSDateTime.from_csv,
        'temp_in_max_ave'      : float,
        'abs_pressure_ave'     : float,
        'abs_pressure_min'     : float,
        'abs_pressure_min_t'   : WSDateTime.from_csv,
        'abs_pressure_max'     : float,
        'abs_pressure_max_t'   : WSDateTime.from_csv,
        'rel_pressure_ave'     : float,
        'rel_pressure_min'     : float,
        'rel_pressure_min_t'   : WSDateTime.from_csv,
        'rel_pressure_max'     : float,
        'rel_pressure_max_t'   : WSDateTime.from_csv,
        'wind_ave'             : float,
        'wind_gust'            : float,
        'wind_gust_t'          : WSDateTime.from_csv,
        'wind_dir'             : float,
        'rain'                 : float,
        'rain_days'            : int,
        'illuminance_ave'      : float,
        'illuminance_max_lo'   : float,
        'illuminance_max_lo_t' : WSDateTime.from_csv,
        'illuminance_max_hi'   : float,
        'illuminance_max_hi_t' : WSDateTime.from_csv,
        'illuminance_max_ave'  : float,
        'uv_ave'               : float,
        'uv_max_lo'            : int,
        'uv_max_lo_t'          : WSDateTime.from_csv,
        'uv_max_hi'            : int,
        'uv_max_hi_t'          : WSDateTime.from_csv,
        'uv_max_ave'           : float,
        }

    def _get_cache_path(self, target_date):
        # one file per year
        path = os.path.join(self._root_dir,
                            target_date.strftime("%Y-01-01.txt"))
        lo = target_date.replace(month=1, day=1)
        if lo.year < MAXYEAR:
            hi = lo.replace(year=lo.year+1)
        else:
            hi = lo
            lo = hi.replace(year=hi.year-1)
        return path, lo, hi


@contextmanager
def pywws_context(data_dir):
    class PywwsContext(object):
        pass

    ctx = PywwsContext()
    # open params and status files
    ctx.params = ParamStore(data_dir, 'weather.ini')
    ctx.status = ParamStore(data_dir, 'status.ini')
    # open data file stores
    ctx.raw_data = RawStore(data_dir)
    ctx.calib_data = CalibStore(data_dir)
    ctx.hourly_data = HourlyStore(data_dir)
    ctx.daily_data = DailyStore(data_dir)
    ctx.monthly_data = MonthlyStore(data_dir)
    # create an event to shutdown threads
    ctx.shutdown = threading.Event()
    # return control to main program
    try:
        yield ctx
    finally:
        # signal threads to terminate
        ctx.shutdown.set()
        # wait for threads to terminate
        for thread in threading.enumerate():
            if thread == threading.current_thread():
                continue
            thread.join()
        # flush all unsaved data
        ctx.params.flush()
        ctx.status.flush()
        ctx.raw_data.flush()
        ctx.calib_data.flush()
        ctx.hourly_data.flush()
        ctx.daily_data.flush()
        ctx.monthly_data.flush()
