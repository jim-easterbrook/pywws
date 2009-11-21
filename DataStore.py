"""
DataStore.py - stores readings in easy to access files

A separate file is used for each day's data, to keep memory load
reasonable. One day at a time is held in memory, and saved to disc
when another day needs to be accessed.

Data is accessed in a cross between dictionary and list behaviour.
The following are all valid:
# get value nearest 9:30 on Christmas day
data[data.nearest(datetime(2008, 12, 25, 9, 30))]
# get entire array, equivalent to data[:] or just data
data[datetime.min:datetime.max]
# get last 12 hours of data
data[datetime.utcnow() - timedelta(hours=12):]
"""

from ConfigParser import SafeConfigParser
import csv
from datetime import date, datetime, timedelta
import os
import sys
import time

def safestrptime(date_string, format="%Y-%m-%d %H:%M:%S"):
    return datetime(*(time.strptime(date_string, format)[0:6]))
class params:
    def __init__(self, root_dir):
        """Parameters are stored in a file "weather.ini" in root_dir."""
        if not os.path.isdir(root_dir):
            os.makedirs(root_dir)
        self._path = os.path.join(root_dir, 'weather.ini')
        self._dirty = False
        # open config file
        self._config = SafeConfigParser()
        self._config.read(self._path)
    def __del__(self):
        if self._dirty:
            of = open(self._path, 'w')
            self._config.write(of)
            of.close()
    def get(self, section, option, default=None):
        """
        Get a parameter value and return a string.

        If default is specified and section or option are not defined
        in the weather.ini file, they are created and set to default,
        which is then the return value.
        """
        if default and not self._config.has_option(section, option):
            self.set(section, option, default)
        return self._config.get(section, option)
    def set(self, section, option, value):
        """Set option in section to string value."""
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, option, value)
        self._dirty = True
class core_store:
    def __init__(self, root_dir):
        self._root_dir = root_dir
        self._one_day = timedelta(days=1)
        # get conservative first and last days for which data (might) exist
        self._fst_day = date.max.toordinal() - 1
        self._lst_day = date.min.toordinal() + 1
        for root, dirs, files in os.walk(self._root_dir):
            dirs.sort()
            files.sort()
            if len(files) > 0:
                path, lo, hi = self._get_cache_path(
                    safestrptime(files[0], "%Y-%m-%d.txt").date())
                self._fst_day = lo
                break
        for root, dirs, files in os.walk(self._root_dir):
            dirs.sort()
            dirs.reverse()
            files.sort()
            if len(files) > 0:
                path, lo, hi = self._get_cache_path(
                    safestrptime(files[-1], "%Y-%m-%d.txt").date())
                self._lst_day = hi
                break
        # initialise cache
        self._cache = []
        self._cache_ptr = 0
        self._cache_lo = date.max.toordinal()
        self._cache_hi = date.min.toordinal()
        self._cache_dirty = False
    def __del__(self):
        self._save()
    def _get_slice(self, i):
        a = i.start
        b = i.stop
        if i.step != None:
            raise TypeError("slice step not permitted")
        if a == None:
            a = datetime.min
        if b == None:
            b = datetime.max
        if not isinstance(a, datetime) or not isinstance(b, datetime):
            raise TypeError("slice indices must be %s or None" % (datetime))
        # go to start of slice
        if a.toordinal() >= self._fst_day:
            self._set_cache_ptr(a)
        else:
            if self._fst_day < self._cache_lo or self._fst_day >= self._cache_hi:
                self._save()
                self._load(date.fromordinal(self._fst_day))
            self._cache_ptr = 0
        # iterate over complete caches
        lst_day = min(b.toordinal(), self._lst_day - 1)
        while self._cache_hi <= lst_day:
            while self._cache_ptr < len(self._cache):
                yield self._cache[self._cache_ptr]
                self._cache_ptr += 1
            self._load(date.fromordinal(self._cache_hi))
            self._cache_ptr = 0
        # iterate over part of cache
        while self._cache_ptr < len(self._cache):
            if self._cache[self._cache_ptr]['idx'] >= b:
                return
            yield self._cache[self._cache_ptr]
            self._cache_ptr += 1
        return
    def __getitem__(self, i):
        """Return the data item or items with index i.

        i must be a datetime object or a slice.
        If i is a single datetime then a value with that index must exist."""
        if isinstance(i, slice):
            return self._get_slice(i)
        if not isinstance(i, datetime):
            raise TypeError("list indices must be %s" % (datetime))
        self._set_cache_ptr(i)
        if self._cache_ptr >= len(self._cache) or \
           self._cache[self._cache_ptr]['idx'] != i:
            raise KeyError(i)
        return self._cache[self._cache_ptr]
    def __setitem__(self, i, x):
        """Store a value x with index i.

        i must be a datetime object.
        If there is already a value with index i, it is overwritten.
        """
        if not isinstance(i, datetime):
            raise TypeError("index '%s' is not %s" % (i, datetime))
        x['idx'] = i
        self._set_cache_ptr(i)
        if len(self._cache) == 0:
            self._fst_day = min(self._fst_day, self._cache_lo)
            self._lst_day = max(self._lst_day, self._cache_hi)
        if self._cache_ptr < len(self._cache) and \
           self._cache[self._cache_ptr]['idx'] == i:
            self._cache[self._cache_ptr] = x
        else:
            self._cache.insert(self._cache_ptr, x)
        self._cache_dirty = True
    def __delitem__(self, i):
        """Delete the value with index i.

        i must be a datetime object.
        A value with that index must exist.
        """
        if not isinstance(i, datetime):
            raise TypeError("list indices must be %s" % (datetime))
        self._set_cache_ptr(i)
        if self._cache_ptr >= len(self._cache) or \
           self._cache[self._cache_ptr]['idx'] != i:
            raise KeyError(i)
        del self._cache[self._cache_ptr]
        self._cache_dirty = True
    def before(self, idx):
        """Return datetime of newest existing data record whose
        datetime is < idx.

        Might not even be in the same year! If no such record exists,
        return None."""
        if not isinstance(idx, datetime):
            raise TypeError("'%s' is not %s" % (idx, datetime))
        day = min(idx.toordinal(), self._lst_day - 1)
        while day >= self._fst_day:
            if day < self._cache_lo or day >= self._cache_hi:
                self._save()
                self._load(date.fromordinal(day))
            self._cache_ptr = len(self._cache)
            while self._cache_ptr > 0:
                self._cache_ptr -= 1
                result = self._cache[self._cache_ptr]['idx']
                if result < idx:
                    return result
            day = self._cache_lo - 1
        return None
    def after(self, idx):
        """Return datetime of oldest existing data record whose
        datetime is >= idx.

        Might not even be in the same year! If no such record exists,
        return None."""
        if not isinstance(idx, datetime):
            raise TypeError("'%s' is not %s" % (idx, datetime))
        day = max(idx.toordinal(), self._fst_day)
        while day < self._lst_day:
            if day < self._cache_lo or day >= self._cache_hi:
                self._save()
                self._load(date.fromordinal(day))
            self._cache_ptr = 0
            while self._cache_ptr < len(self._cache):
                result = self._cache[self._cache_ptr]['idx']
                if result >= idx:
                    return result
                self._cache_ptr += 1
            day = self._cache_hi
        return None
    def nearest(self, idx):
        """Return datetime of record whose datetime is nearest idx."""
        hi = self.after(idx)
        lo = self.before(idx)
        if hi == None:
            return lo
        if lo == None:
            return hi
        if abs(hi - idx) < abs(lo - idx):
            return hi
        return lo
    def _set_cache_ptr(self, i):
        day = i.toordinal()
        if day < self._cache_lo or day >= self._cache_hi:
            self._save()
            self._load(i)
        if self._cache_ptr < len(self._cache) and \
              self._cache[self._cache_ptr]['idx'] < i:
            self._cache_ptr += 1
            while self._cache_ptr < len(self._cache) and \
                  self._cache[self._cache_ptr]['idx'] < i:
                self._cache_ptr += 1
            return
        while self._cache_ptr > 0 and self._cache[self._cache_ptr-1]['idx'] >= i:
            self._cache_ptr -= 1
    def _load(self, target_date):
        self._cache = []
        self._cache_ptr = 0
        self._cache_path, self._cache_lo, self._cache_hi = self._get_cache_path(target_date)
        if os.path.exists(self._cache_path):
            reader = csv.DictReader(
                open(self._cache_path, 'rb'), self.key_list, quoting=csv.QUOTE_NONE)
            for row in reader:
                for key in self.key_list:
                    if row[key] == '':
                        row[key] = None
                    else:
                        row[key] = self.conv[key](row[key])
                self._cache.append(row)
    def _save(self):
        if not self._cache_dirty:
            return
        self._cache_dirty = False
        if len(self._cache) == 0:
            if os.path.exists(self._cache_path):
                # existing data has been wiped, so delete file
                os.unlink(self._cache_path)
            return
        dir = os.path.dirname(self._cache_path)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        writer = csv.DictWriter(
            open(self._cache_path, 'wb'), self.key_list, quoting=csv.QUOTE_NONE)
        writer.writerows(self._cache)
    def _get_cache_path(self, target_date):
        # default implementation - one file per day
        path = os.path.join(self._root_dir,
                            target_date.strftime("%Y"),
                            target_date.strftime("%Y-%m"),
                            target_date.strftime("%Y-%m-%d.txt"))
        lo = target_date.toordinal()
        hi = lo + 1
        return path, lo, hi
class data_store(core_store):
    """Stores raw weather station data."""
    def __init__(self, root_dir):
        core_store.__init__(self, os.path.join(root_dir, 'raw'))
    key_list = ['idx', 'delay', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
                'abs_pressure', 'wind_ave', 'wind_gust', 'wind_dir', 'rain', 'status']
    conv = {
        'idx'          : safestrptime,
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
        'status'       : int,
        }
class hourly_store(core_store):
    """Stores hourly summary weather station data."""
    def __init__(self, root_dir):
        core_store.__init__(self, os.path.join(root_dir, 'hourly'))
    key_list = ['idx', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
                'abs_pressure', 'rel_pressure', 'pressure_trend',
                'wind_ave', 'wind_gust', 'wind_dir', 'rain']
    conv = {
        'idx'               : safestrptime,
        'hum_in'            : int,
        'temp_in'           : float,
        'hum_out'           : int,
        'temp_out'          : float,
        'abs_pressure'      : float,
        'rel_pressure'      : float,
        'pressure_trend'    : float,
        'wind_ave'          : float,
        'wind_gust'         : float,
        'wind_dir'          : int,
        'rain'              : float,
        }
class daily_store(core_store):
    """Stores daily summary weather station data."""
    def __init__(self, root_dir):
        core_store.__init__(self, os.path.join(root_dir, 'daily'))
    key_list = ['idx', 'start', 'temp_out_min_t', 'temp_out_min',
                'temp_out_max_t', 'temp_out_max',
                'wind_ave', 'wind_gust_t', 'wind_gust', 'wind_dir', 'rain']
    conv = {
        'idx'               : safestrptime,
        'start'             : safestrptime,
        'temp_out_min_t'    : safestrptime,
        'temp_out_min'      : float,
        'temp_out_max_t'    : safestrptime,
        'temp_out_max'      : float,
        'wind_ave'          : float,
        'wind_gust_t'       : safestrptime,
        'wind_gust'         : float,
        'wind_dir'          : int,
        'rain'              : float,
        }
    def _get_cache_path(self, target_date):
        # one file per month
        path = os.path.join(self._root_dir,
                            target_date.strftime("%Y"),
                            target_date.strftime("%Y-%m-01.txt"))
        lo = target_date.replace(day=1)
        if lo.month < 12:
            hi = lo.replace(month=lo.month+1)
        else:
            hi = lo.replace(year=lo.year+1, month=1)
        return path, lo.toordinal(), hi.toordinal()
class monthly_store(core_store):
    """Stores monthly summary weather station data."""
    def __init__(self, root_dir):
        core_store.__init__(self, os.path.join(root_dir, 'monthly'))
    key_list = ['idx', 'start',
                'temp_out_min_lo_t', 'temp_out_min_lo',
                'temp_out_min_hi_t', 'temp_out_min_hi', 'temp_out_min_ave',
                'temp_out_max_lo_t', 'temp_out_max_lo',
                'temp_out_max_hi_t', 'temp_out_max_hi', 'temp_out_max_ave',
                'rain']
    conv = {
        'idx'               : safestrptime,
        'start'             : safestrptime,
        'temp_out_min_lo_t' : safestrptime,
        'temp_out_min_lo'   : float,
        'temp_out_min_hi_t' : safestrptime,
        'temp_out_min_hi'   : float,
        'temp_out_min_ave'  : float,
        'temp_out_max_lo_t' : safestrptime,
        'temp_out_max_lo'   : float,
        'temp_out_max_hi_t' : safestrptime,
        'temp_out_max_hi'   : float,
        'temp_out_max_ave'  : float,
        'rain'              : float,
        }
    def _get_cache_path(self, target_date):
        # one file per year
        path = os.path.join(self._root_dir,
                            target_date.strftime("%Y-01-01.txt"))
        lo = target_date.replace(month=1, day=1)
        hi = lo.replace(year=lo.year+1)
        return path, lo.toordinal(), hi.toordinal()
