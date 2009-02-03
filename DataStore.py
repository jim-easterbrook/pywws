"""
DataStore.py - stores readings in easy to access files

This module is at the core of the weather station software. It stores
data on disc, but without the overhead of a full scale database
system. It is designed to run on a small memory machine such as a
router. To minimise memory usage it only loads one day's worth of data
at a time into memory.

From a "user" point of view, the data is accessed as a cross between a
list and a dictionary. Each data record is indexed by a <a
href="http://docs.python.org/library/datetime.html#datetime-objects">datetime</a>
object (dictionary behaviour), but records are stored in order and can
be accessed as slices (list behaviour).


A separate file is used for each day's data, to keep memory load
reasonable. One day at a time is held in memory, and saved to disc
when another day needs to be accessed.

Data is accessed in a cross between dictionary and list behaviour.
"""

from ConfigParser import SafeConfigParser
import csv
from datetime import date, datetime
import os
import sys

class params():
    def __init__(self, root_dir):
        """Parameters are stored in a file "weather.ini" in root_dir."""
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
class core_store():
    def __init__(self, root_dir):
        self._root_dir = root_dir
        # get first and last day for which data exists
        self._fst_day = datetime.max.toordinal()
        self._lst_day = datetime.min.toordinal()
        for root, dirs, files in os.walk(self._root_dir):
            dirs.sort()
            files.sort()
            if len(files) > 0:
                self._fst_day = datetime.strptime(files[0], "%Y-%m-%d.txt").toordinal()
                break
        for root, dirs, files in os.walk(self._root_dir):
            dirs.sort()
            dirs.reverse()
            files.sort()
            if len(files) > 0:
                self._lst_day = datetime.strptime(files[-1], "%Y-%m-%d.txt").toordinal()
                break
        # initialise cache
        self._cache = []
        self._cache_ptr = 0
        self._cache_day = None
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
        start_day = max(a.toordinal(), self._fst_day)
        stop_day = min(b.toordinal(), self._lst_day)
        day = start_day
        while day <= stop_day:
            self._set_cache(day)
            if day == start_day:
                self._set_cache_ptr(a)
            else:
                self._cache_ptr = 0
            if day == stop_day:
                while self._cache_ptr < len(self._cache):
                    if self._cache[self._cache_ptr]['idx'] >= b:
                        return
                    yield self._cache[self._cache_ptr]
                    self._cache_ptr += 1
                return
            while self._cache_ptr < len(self._cache):
                yield self._cache[self._cache_ptr]
                self._cache_ptr += 1
            day += 1
    def __getitem__(self, i):
        if isinstance(i, slice):
            return self._get_slice(i)
        if not isinstance(i, datetime):
            raise TypeError("list indices must be %s" % (datetime))
        day = i.toordinal()
        if day < self._fst_day or day > self._lst_day:
            raise KeyError(i)
        self._set_cache(day)
        self._set_cache_ptr(i)
        if self._cache_ptr >= len(self._cache) or \
           self._cache[self._cache_ptr]['idx'] != i:
            raise KeyError(i)
        return self._cache[self._cache_ptr]
    def __setitem__(self, i, x):
        if not isinstance(i, datetime):
            raise TypeError("index '%s' is not %s" % (i, datetime))
        x['idx'] = i
        day = i.toordinal()
        self._fst_day = min(self._fst_day, day)
        self._lst_day = max(self._lst_day, day)
        self._set_cache(day)
        self._set_cache_ptr(i)
        if self._cache_ptr < len(self._cache) and \
           self._cache[self._cache_ptr]['idx'] == i:
            self._cache[self._cache_ptr] = x
        else:
            self._cache.insert(self._cache_ptr, x)
        self._cache_dirty = True
    def __delitem__(self, i):
        if not isinstance(i, datetime):
            raise TypeError("list indices must be %s" % (datetime))
        day = i.toordinal()
        if day < self._fst_day or day > self._lst_day:
            raise KeyError(i)
        self._set_cache(day)
        self._set_cache_ptr(i)
        if self._cache_ptr >= len(self._cache) or \
           self._cache[self._cache_ptr]['idx'] != i:
            raise KeyError(i)
        del self._cache[self._cache_ptr]
        self._cache_dirty = True
    def before(self, idx):
        # returns datetime of newest existing data record whose datetime
        # is < idx. Might not even be in the same year!
        # If no such record exists, returns None
        if not isinstance(idx, datetime):
            raise TypeError("'%s' is not %s" % (idx, datetime))
        target = idx.toordinal()
        day = min(target, self._lst_day)
        while day >= self._fst_day:
            self._set_cache(day)
            if len(self._cache) > 0:
                if day < target:
                    return self._cache[-1]['idx']
                ptr = len(self._cache)
                while ptr > 0:
                    ptr -= 1
                    if self._cache[ptr]['idx'] < idx:
                        return self._cache[ptr]['idx']
            day -= 1
        return None
    def after(self, idx):
        # returns datetime of oldest existing data record whose datetime
        # is >= idx. Might not even be in the same year!
        # If no such record exists, returns None
        if not isinstance(idx, datetime):
            raise TypeError("'%s' is not %s" % (idx, datetime))
        target = idx.toordinal()
        day = max(target, self._fst_day)
        while day <= self._lst_day:
            self._set_cache(day)
            if len(self._cache) > 0:
                if day > target:
                    return self._cache[0]['idx']
                ptr = 0
                while ptr < len(self._cache):
                    if self._cache[ptr]['idx'] >= idx:
                        return self._cache[ptr]['idx']
                    ptr += 1
            day += 1
        return None
    def nearest(self, idx):
        # returns datetime of record whose datetime is nearest idx
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
        while self._cache_ptr > 0 and self._cache[self._cache_ptr-1]['idx'] >= i:
            self._cache_ptr -= 1
        while self._cache_ptr < len(self._cache) and \
              self._cache[self._cache_ptr]['idx'] < i:
            self._cache_ptr += 1
    def _set_cache(self, target_day):
        if target_day == self._cache_day:
            return
        self._save()
        self._cache = []
        self._cache_day = target_day
        self._cache_ptr = 0
        self._load()
    def _load(self):
#        print "load cache", self._cache_day, date.fromordinal(self._cache_day)
        path = self._path(self._cache_day)
        if os.path.exists(path):
            reader = csv.DictReader(open(path, 'rb'), self.key_list,
                                    quoting=csv.QUOTE_NONE)
            for row in reader:
                for key, type in self.types.items():
                    if row[key] == '':
                        row[key] = None
                    elif type == 'float':
                        row[key] = float(row[key])
                    elif type == 'int':
                        row[key] = int(row[key])
                    elif type == 'time':
                        row[key] = datetime.strptime(row[key], "%Y-%m-%d %H:%M:%S")
                    else:
                        raise TypeError('Type not recognised for %s', key)
                self._cache.append(row)
    def _save(self):
        if not self._cache_dirty:
            return
#        print "save cache", self._cache_day, date.fromordinal(self._cache_day)
        self._cache_dirty = False
        path = self._path(self._cache_day)
        if len(self._cache) == 0:
            if os.path.exists(path):
                # existing data has been wiped, so delete file
                os.unlink(path)
            return
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        writer = csv.DictWriter(open(path, 'wb'), self.key_list,
                                quoting=csv.QUOTE_NONE)
        writer.writerows(self._cache)
    def _path(self, day):
        # returns file name for given day
        target_date = date.fromordinal(day)
        return os.path.join(self._root_dir,
                            target_date.strftime("%Y"),
                            target_date.strftime("%Y-%m"),
                            target_date.strftime("%Y-%m-%d.txt"))
class data_store(core_store):
    def __init__(self, root_dir):
        core_store.__init__(self, os.path.join(root_dir, 'raw'))
    key_list = ['idx', 'delay', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
                'pressure', 'wind_ave', 'wind_gust', 'wind_dir', 'rain', 'status']
    types = {
        'idx'       : 'time',
        'delay'     : 'int',
        'hum_in'    : 'int',
        'temp_in'   : 'float',
        'hum_out'   : 'int',
        'temp_out'  : 'float',
        'pressure'  : 'float',
        'wind_ave'  : 'float',
        'wind_gust' : 'float',
        'wind_dir'  : 'int',
        'rain'      : 'float',
        'status'    : 'int',
        }
class hourly_store(core_store):
    def __init__(self, root_dir):
        core_store.__init__(self, os.path.join(root_dir, 'hourly'))
    key_list = ['idx', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
                'pressure', 'pressure_trend', 'wind_ave', 'wind_gust', 'wind_dir',
                'rain']
    types = {
        'idx'               : 'time',
        'hum_in'            : 'int',
        'temp_in'           : 'float',
        'hum_out'           : 'int',
        'temp_out'          : 'float',
        'pressure'          : 'float',
        'pressure_trend'    : 'float',
        'wind_ave'          : 'float',
        'wind_gust'         : 'float',
        'wind_dir'          : 'int',
        'rain'              : 'float',
        }
class daily_store(core_store):
    def __init__(self, root_dir):
        core_store.__init__(self, os.path.join(root_dir, 'daily'))
    key_list = ['idx', 'temp_out_min_t', 'temp_out_min',
                'temp_out_max_t', 'temp_out_max',
                'wind_ave', 'wind_gust_t', 'wind_gust', 'wind_dir', 'rain']
    types = {
        'idx'               : 'time',
        'temp_out_min_t'    : 'time',
        'temp_out_min'      : 'float',
        'temp_out_max_t'    : 'time',
        'temp_out_max'      : 'float',
        'wind_ave'          : 'float',
        'wind_gust_t'       : 'time',
        'wind_gust'         : 'float',
        'wind_dir'          : 'int',
        'rain'              : 'float',
        }
