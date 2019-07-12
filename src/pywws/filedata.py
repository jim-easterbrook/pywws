# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-19  pywws contributors

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

"""Store weather data in easy to access files

Introduction
------------

This module is at the core of pywws file based storage.
It stores data on disc, but without the overhead of a full scale
database system. I have designed it to run on a small memory machine
such as a Raspberry Pi or even a router. To minimise memory usage it
only loads one day's worth of raw data at a time into memory.

From a "user" point of view, the data is accessed as a cross between a
list and a dictionary. Each data record is indexed by a
:py:class:`datetime.datetime` object (dictionary behaviour), but
records are stored in order and can be accessed as slices (list
behaviour).

For example, to access the hourly data for Christmas day 2009, one
might do the following::

  from datetime import datetime
  import pywws.filedata
  hourly = pywws.filedata.HourlyStore('weather_data')
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

import csv
from datetime import date, datetime, timedelta, MAXYEAR
import logging
import os
import sys
import time

from pywws.constants import DAY
from pywws.weatherstation import WSDateTime, WSFloat, WSInt, WSStatus

logger = logging.getLogger(__name__)


class _Cache(object):
    def __init__(self):
        self.data = []
        self.path = ''
        self.lo = date.max
        self.hi = date.min
        self.dirty = False

    def copy(self, other):
        self.data = other.data
        self.path = other.path
        self.lo = other.lo
        self.hi = other.hi
        self.dirty = False

    def get_ptr(self, idx):
        """Return index at which to insert a record with timestamp idx
        and boolean indicating if there is already data with that
        timestamp.

        """
        hi = len(self.data) - 1
        if hi < 0 or self.data[0]['idx'] > idx:
            return 0, False
        if self.data[0]['idx'] == idx:
            return 0, True
        if self.data[hi]['idx'] < idx:
            return hi + 1, False
        lo = 0
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.data[mid]['idx'] < idx:
                lo = mid
            elif self.data[mid]['idx'] == idx:
                return mid, True
            else:
                hi = mid
        return hi, self.data[hi]['idx'] == idx


class CoreStore(object):
    def __init__(self, root_dir):
        self._root_dir = os.path.abspath(os.path.join(root_dir, self.dir_name))
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
        # use separate cache as something might change self._rd_cache
        # during yield
        cache = _Cache()
        # go to start of slice
        start, exact = self._get_cache_ptr(cache, a)
        # iterate over complete caches
        while cache.hi <= b.date():
            for data in cache.data[start:]:
                yield data
            if cache.hi >= self._hi_limit:
                return
            self._load(cache, cache.hi)
            start = 0
        # iterate over part of cache
        for data in cache.data[start:]:
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
        cache = self._rd_cache
        ptr, exact = self._get_cache_ptr(cache, i)
        if not exact:
            raise KeyError(i)
        return cache.data[ptr]

    def __setitem__(self, i, x):
        """Store a value x with index i.

        i must be a datetime object.
        If there is already a value with index i, it is overwritten.
        """
        if not isinstance(i, datetime):
            raise TypeError("index '%s' is not %s" % (i, datetime))
        x['idx'] = i
        cache = self._wr_cache
        ptr, exact = self._get_cache_ptr(cache, i)
        if exact:
            cache.data[ptr] = x
        else:
            cache.data.insert(ptr, x)
        cache.dirty = True

    def _del_slice(self, i):
        a, b = self._slice(i)
        if a > b:
            return
        # go to start of slice
        cache = self._wr_cache
        start, exact = self._get_cache_ptr(cache, a)
        # delete to end of cache
        while cache.hi <= b.date():
            del cache.data[start:]
            cache.dirty = True
            if cache.hi >= self._hi_limit:
                return
            self._load(cache, cache.hi)
            start = 0
        # delete part of cache
        stop, exact = cache.get_ptr(b)
        del cache.data[start:stop]
        cache.dirty = True

    def __delitem__(self, i):
        """Delete the data item or items with index i.

        i must be a datetime object or a slice.
        If i is a single datetime then a value with that index must exist."""
        if isinstance(i, slice):
            return self._del_slice(i)
        if not isinstance(i, datetime):
            raise TypeError("list indices must be %s" % (datetime))
        cache = self._wr_cache
        ptr, exact = self._get_cache_ptr(cache, i)
        if not exact:
            raise KeyError(i)
        del cache.data[ptr]
        cache.dirty = True

    def before(self, idx):
        """Return datetime of newest existing data record whose
        datetime is < idx.

        Might not even be in the same year! If no such record exists,
        return None."""
        if not isinstance(idx, datetime):
            raise TypeError("'%s' is not %s" % (idx, datetime))
        day = min(idx.date(), self._hi_limit - DAY)
        cache = self._rd_cache
        while day >= self._lo_limit:
            if day < cache.lo or day >= cache.hi:
                self._load(cache, day)
            ptr, exact = cache.get_ptr(idx)
            if ptr > 0:
                return cache.data[ptr - 1]['idx']
            day = cache.lo - DAY
        return None

    def after(self, idx):
        """Return datetime of oldest existing data record whose
        datetime is >= idx.

        Might not even be in the same year! If no such record exists,
        return None."""
        if not isinstance(idx, datetime):
            raise TypeError("'%s' is not %s" % (idx, datetime))
        day = max(idx.date(), self._lo_limit)
        cache = self._rd_cache
        while day < self._hi_limit:
            if day < cache.lo or day >= cache.hi:
                self._load(cache, day)
            ptr, exact = cache.get_ptr(idx)
            if ptr < len(cache.data):
                return cache.data[ptr]['idx']
            day = cache.hi
        return None

    def nearest(self, idx):
        """Return datetime of record whose datetime is nearest idx."""
        hi = self.after(idx)
        if hi == idx:
            return hi
        lo = self.before(idx)
        if hi is None:
            return lo
        if lo is None:
            return hi
        if (hi - idx) < (idx - lo):
            return hi
        return lo

    def _get_cache_ptr(self, cache, i):
        day = i.date()
        if day < cache.lo or day >= cache.hi:
            self._load(cache, day)
            if cache.lo < self._lo_limit:
                self._lo_limit = cache.lo
                self._lo_limit_dt = datetime(
                    cache.lo.year, cache.lo.month, cache.lo.day)
            if cache.hi > self._hi_limit:
                self._hi_limit = cache.hi
                self._hi_limit_dt = datetime(
                    cache.hi.year, cache.hi.month, cache.hi.day)
        return cache.get_ptr(i)

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
        cache.path, cache.lo, cache.hi = new_path, new_lo, new_hi
        if not os.path.exists(cache.path):
            return
        if sys.version_info[0] >= 3:
            kwds = {'mode': 'r', 'newline': ''}
        else:
            kwds = {'mode': 'rb'}
        row_lengths = (len(self.key_list),
                       len(self.key_list) - self.solar_items)
        with open(cache.path, **kwds) as csvfile:
            reader = csv.reader(csvfile, quoting=csv.QUOTE_NONE)
            for row in reader:
                if len(row) not in row_lengths:
                    logger.error('Invalid %s data at %s', self.dir_name, row[0])
                    continue
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

    def __iter__(self):
        """Return an iterator which yields all items in the data store
        sequntially. Equivalent to: for item in dataset[:]: yield item"""
        for item in self[:]: yield item

    def update(self, E):
        """D.update(E) -> None. Equivelent to: for k in E: D[ k['idx'] ] = k"

        Update D from list-like iterable E containing dicts.
        Pre-existing items being overwritten.
        Dicts are assumed to contain all appropriate keys and values."""
        for k in E:
            self[ k['idx'] ] = k

    def clear(self):
        """Clears all data from the data store permanently"""
        for root, dirs, files in os.walk(self._root_dir, topdown=False):
            for file in files:
                os.unlink(os.path.join(root, file))
            os.rmdir(root)
        # Get the root dir back and re-initialise to start again
        root_dir = os.path.abspath(
            os.path.join(self._root_dir, os.pardir))
        self.__init__(root_dir)

class RawStore(CoreStore):
    """Stores raw weather station data."""
    dir_name = 'raw'
    key_list = [
        'idx', 'delay', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
        'abs_pressure', 'wind_ave', 'wind_gust', 'wind_dir', 'rain',
        'status', 'illuminance', 'uv',
        ]
    solar_items = 2
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
    solar_items = 2
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
    solar_items = 2
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
    solar_items = 6
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
    solar_items = 12
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

