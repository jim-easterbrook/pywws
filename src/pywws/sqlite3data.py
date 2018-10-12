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

"""Store weather data in an SQLite3 database file.

Introduction
------------

This module is an alternative to the pywws file based storage system.
It stores data using the mature SQLite3 database system, but with
underlying queries wrapped so the user need not know about them.

This module is currently only compatible with Python3.6 and later
primarily due to the extensive use of f-strings and compound with statements,
but the core functionaty and libraries are Py2 compatible so it is possible to
backport and refactor to Python2 as a future enhancement.

It should also be possible for this module to form the basis of a
full client-server based SQL module using, for example, MySQL etc.

The Python builtin sqlite3 module is used which has a threadsafety of 1,
therefore this module creates a connection with every Store (sub)class instance.
This however brings concurrancy issues and so this module makes use of the
underlying sqlite3's Write-Ahead-Loging and Shared Cache modes to relieve this.
These rely on up to date sqlite3 libraries and may not work on older networked
drives which do not support the right locking semantics required by sqlite3.


The external API is as per the original pywws file store, but with
some enhancements so as to behave more like a mapping container (dict).

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

import sqlite3
import os.path
from threading import RLock
from datetime import date, datetime, timedelta, timezone
from pywws.weatherstation import WSDateTime, WSFloat, WSInt, WSStatus


# Data type adapt: Python ==> SQLite3
def _adapt_WSDateTime(dt):
	'''Return unix timestamp of the datetime like input. If conversion overflows high, return sint64_max , if underflows, return 0'''
	try: ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
	except (OverflowError,OSError):
		if dt < datetime.now(): ts = 0
		else: ts = 2**63-1
	return ts

def _adapt_WSStatus(status):
	'''Return integer represending WSStatus dictionary input'''
	return int(WSStatus.to_csv(status))

# Data type convert SQLite3 ==> Python
def _convert_WSDateTime(b):
	'''Return a WSDateTime object for a given unix timestamp'''
	return WSDateTime.utcfromtimestamp(int(b))

def _convert_WSStatus(b):
	'''Return a WSStatus dictionary for a given number'''
	return WSStatus.from_csv(b)

def _convert_WSFloat(b):
	'''Return a WSFloat for the given input'''
	return WSFloat(b)

def _convert_WSInt(b):
	'''Return WSInt for the given input'''
	return WSInt(b)

sqlite3.enable_shared_cache(True)

sqlite3.register_adapter(datetime, _adapt_WSDateTime)
sqlite3.register_adapter(WSDateTime, _adapt_WSDateTime)
sqlite3.register_adapter(WSStatus, _adapt_WSStatus)
sqlite3.register_adapter(WSFloat, float)	# This ensures SQLite handles these special types and treats them as standard float
sqlite3.register_adapter(WSInt, int)	# This ensures SQLite handles these special types and treats them as standard int

sqlite3.register_converter('WSDateTime', _convert_WSDateTime)
sqlite3.register_converter('WSStatus', _convert_WSStatus)
sqlite3.register_converter('WSFloat', _convert_WSFloat)
sqlite3.register_converter('WSInt', _convert_WSInt)


class CoreStore(object):
	'''Provides a dictionary/list like interface to an underlying SQLite3 database'''
	key_list = tuple(['idx'])
	conv = {'idx':None}	# This overrides type conversion based on incorrect sql type (i.e. for the primary key)
	table = ''
	_keycol = 'idx'
	if len(key_list) == 0 or len(conv) == 0: raise KeyError("The Key list and Conversion lists are empty.")
	if set(key_list) != conv.keys(): raise KeyError("The Key list and Conversion list don't match.")
	if _keycol not in key_list: raise KeyError(f'Key coloumn "{keycol}" is not in the key list')	# Check that the key coloumn is present

	def __init__(self, dir_name):
		key_list = self.key_list
		conv = self.conv
		table = self.table
		keycol = self._keycol
		dbpath = os.path.abspath(os.path.join(dir_name, 'pywws.db'))
		self._connection = sqlite3.connect(dbpath, detect_types=sqlite3.PARSE_COLNAMES)
		self._connection.row_factory = sqlite3.Row
		con = self._connection
		if con.execute('PRAGMA journal_mode=WAL').fetchone()['journal_mode'] != 'wal': raise TypeError('Database is not in Write-Ahead-Log mode')
		if con.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name=?;', (table,)).fetchone()[0] == 0: con.executescript(f'CREATE TABLE IF NOT EXISTS {table} ( {keycol} INTEGER PRIMARY KEY, {", ".join(f"{key} NUM" for key in conv if key != keycol)} );')
		# Create the table if its not already there. Assume all data fields are NUM so that SQLite can optimise storage as it will choose the smallest integer representation between 8-64bit, while floats are always 64bit. Set idx as a unique integer primary key so searches are faster, storage requirements smaller, the rowid coloumn is eliminated so there is no need for secondary indices. Suitable converters/adapters are then applies.
		sql_key_list = tuple( (row['name'],row['pk']) for row in con.execute('SELECT name, pk FROM PRAGMA_TABLE_INFO(?);', (table,)) )	# Get all coloumns from the database
		sql_pk = tuple( key[0] for key in sql_key_list if key[1] == 1 )	# Fetch the primary key - there should only be one
		if len(sql_pk) != 1 or sql_pk[0] != keycol: raise KeyError('Mismatch between database primary key and what was expected')
		sql_key_list = set( key[0] for key in sql_key_list) # Convert this to just a tuple of keys
		if not conv.keys() <= sql_key_list: raise KeyError('Mismatch between database coloumns and what was expected')	# Check that no coloumns are missing
		self.selallcols = ', '.join(f'{col} AS "{col} [{conv[col]}]"' for col in key_list)	# SQL snippet which casts all coloumns to the correct data types for SELECT * type queries
		self.selkeycol = f'{keycol} AS "{keycol} [{conv[keycol]}]"'	# SQL snippet which casts the key coloum to the correct data type for SELECT {keycol} type queries

	def __del__(self):
		'''Prior to object being deleted, update SQLite statistics, then close connection gracefully'''
		with self._connection as con: con.executescript(f'ANALYZE {self.table}; PRAGMA wal_checkpoint(TRUNCATE);')

	def __len__(self):
		'''Return the exact number of records in the table'''
		return self._connection.execute(f'SELECT COUNT(*) FROM {self.table};').fetchone()[0]	# Direct count of all records - could be slow.
	
	def __length_hint__(self):
		'''Return the approximate table size based on internal database statistics if present, otherwise, find the actual length'''
		# Assuming the database has been analyzed before, the stat1 table should contain the total row count for the table as the first number in the stat coloumn from when it was last analyzed. Very fast but may not be up to date
		try: return int(self._connection.execute('SELECT stat FROM sqlite_stat1 WHERE tbl=?;',(self.table,)).fetchone()[0].split(' ')[0])
		except (TypeError,sqlite3.OperationalError): return self.__len__()

	def _predicate(self, i):
		'''Given a valid datetime or slace, return the predicate portion of the SQL query, a boolean indicating whether multiple items are expected from the result, and a dictionary of parameters for the query'''
		if isinstance(i, slice):
			if i.step is not None: raise TypeError('Slice step not permitted')
			if (i.start is not None and not isinstance(i.start, datetime)) or (i.stop is not None and not isinstance(i.stop, datetime)): raise TypeError(f'Slice indices must be {datetime} or {None}')
			if i.start is not None and i.stop is not None:
				if i.start > i.stop: raise ValueError('Start index is greater than the End index')
				else: predicate = f'WHERE {self._keycol} BETWEEN :start AND :stop'	# F-String substitution of the key coloumn, but the parameters themselves will be substituted by sqlite3
			elif i.start is not None: predicate = f'WHERE {self._keycol} >= :start'	# and therefore i.stop must be None
			elif i.stop is not None: predicate = f'WHERE {self._keycol} <= :stop'	# and therefore i.start must be None
			else: predicate = ''	# both are None, so equivelent to wanting everything
			multi = True
			pred = {'start': i.start, 'stop': i.stop}
		elif isinstance(i, datetime):
			predicate = f'WHERE {self._keycol} = :key'	# F-String substitution of the key coloumn, but the parameters themselves will be substituted by sqlite3
			multi = False
			pred = {'key': i}
		else: raise TypeError(f'List indices must be {datetime}')	# not a slice or a datetime object
		return (predicate, multi, pred)	# predicate is the end of the query string. multi is a boolean indicating whether the result should be iterable or not. pred is a dict of the parameters for substitution

	def __getitem__(self, i):
		'''Return the data item or items with index i. i must be a datetime object or a slice.
		If i is a single datetime then a value with that index must exist.'''
		predicate, multi, params = self._predicate(i)
		results = self._connection.execute(f'SELECT {self.selallcols} FROM {self.table} {predicate};', params)
		if multi: return (dict(row) for row in results)	# If multiple items are expected, give a generator
		else:	# If one item is expected, return it directly
			item = results.fetchone()
			return self.__missing__(i) if item is None else dict(item)

	def __contains__(self, i):
		'''Return True if i is in the table, else False'''
		if self._connection.execute(f'SELECT count(*) FROM {self.table} WHERE {self._keycol} = ?;', (i,)).fetchone()[0] > 0: return True
		else: return False

	def __missing__(self, i):
		raise IndexError(i)

	def __setitem__(self, i, x):
		'''Store a value x with index i. i must be a datetime object.
		If there is already a value with index i, it is overwritten.'''
		if not isinstance(i, datetime): raise TypeError(f'"{i}" is not {datetime}')
		elif not isinstance(x, dict): raise TypeError(f'Values not {dict}')
		x[self._keycol] = i
		with self._connection as con: con.execute(f'INSERT OR REPLACE INTO {self.table} ({", ".join(x)}) VALUES (:{", :".join(x)});', x)

	def update(self, i):
		''' D.update(E) -> None.  Update D from iterable E with pre-existing items being overwritten.
			Elements in E are assumed to be dicts containing the primary key to allow the equivelent of: for k in E: D[k.primary_key] = k'''
		key_list = self.key_list
		datagen = ( {**datum, **{k:None for k in key_list - datum.keys()}} for datum in i )	# Generator which fills in any missing data from the original iterator as it's consumed
		with self._connection as con: con.executemany(f'INSERT OR REPLACE INTO {self.table} ({", ".join(self.key_list)}) VALUES (:{", :".join(self.key_list)});', datagen)

	def __delitem__(self, i):
		'''Delete the data item or items with index i. i must be a datetime object or a slice.
		If i is a single datetime then a value with that index must exist.'''
		predicate, multi, params = self._predicate(i)
		with self._connection as con:
			if con.execute(f'DELETE FROM {self.table} {predicate};', params).rowcount == 0 and multi is False:
				raise KeyError(i)

	def before(self, i):
		'''Return datetime of newest existing data record whose datetime is < idx.
		If no such record exists, return None.'''
		if not isinstance(i, datetime): raise TypeError(f'"{i}" is not {datetime}')
		else: result = self._connection.execute(f'SELECT {self.selkeycol} FROM {self.table} WHERE {self._keycol} < :key ORDER BY {self._keycol} DESC LIMIT 1;', {'key':i}).fetchone()
		return result[self._keycol] if result is not None else None

	def after(self, i):
		'''Return datetime of oldest existing data record whose datetime is >= idx.
		If no such record exists, return None.'''
		if not isinstance(i, datetime): raise TypeError(f'"{i}" is not {datetime}')
		else: result = self._connection.execute(f'SELECT {self.selkeycol} FROM {self.table} WHERE idx >= :key ORDER BY {self._keycol} ASC LIMIT 1;',{'key':i}).fetchone()
		return result[self._keycol] if result is not None else None

	def nearest(self, i):
		'''Return datetime of record whose datetime is nearest idx.'''
		if not isinstance(i, datetime): raise TypeError(f'"{i}" is not {datetime}')
		else: result = self._connection.execute(f'SELECT {self.selkeycol} FROM {self.table} ORDER BY ABS({self._keycol}-:key) ASC LIMIT 1;', {'key':i}).fetchone()
		return result[self._keycol] if result is not None else None

	def flush(self):
		'''Commits any uncommitted data and then flushes the write ahead log'''
		with self._connection as con: con.executescript('PRAGMA wal_checkpoint(TRUNCATE);')	#execute script has implied commit before it

	def keys(self):
		'''D.keys() -> a set-like object providing a view on D's keys'''
		return set( row[self._keycol] for row in self._connection.execute(f'SELECT DISTINCT {self.selkeycol} FROM {self.table} ORDER BY {self._keycol} ASC;') )

	def __iter__(self):
		'''Iterates over all rows in ascending order of key coloumn'''
		for row in self._connection.execute(f'SELECT {self.selallcols} FROM {self.table} ORDER BY {self._keycol} ASC;'): yield dict(row)

	def __reversed__(self):
		'''Iterates over all rows in decending order of key coloumn'''
		for row in self._connection.execute(f'SELECT {self.selallcols} FROM {self.table} ORDER BY {self._keycol} DESC;'): yield dict(row)

	def values(self):
		'''D.values() -> an object providing a view on D's values'''
		yield from self.__iter__()

	def items(self):
		'''D.items() -> a set-like object providing a view on D's items'''
		keycol = self._keycol
		for row in self.__iter__(): yield (row[keycol], dict(row))

	def get(self, key, default=None):
		'''D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.'''
		try: return self[key]
		except (KeyError, IndexError): return default

	def clear(self):
		'''S.clear() -> None -- remove all items from S'''
		with self._connection as con: con.execute(f'DELETE FROM {self.table};')

	def setdefault(self, key, default=None):
		'''D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D'''
		try: return self[key]
		except (KeyError, IndexError): self[key] = default
		return default

	__marker = object()
	def pop(self, key, default=__marker):
		'''D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
		If key is not found, d is returned if given, otherwise KeyError is raised.'''
		try:
			value = self[key]
			del self[key]
			return value
		except (KeyError, IndexError):
			if default is self.__marker: raise
			else: return default

	def popitem(self):
		'''D.popitem() -> (k, v), remove and return some (key, value) pair as a 2-tuple; but raise KeyError if D is empty.'''
		try:
			value = next(iter(self))
			key = value[self._keycol]
		except StopIteration: raise KeyError from None
		del self[key]
		return key, value


class RawStore(CoreStore):
	'''Stores raw weather station data.'''
	table = 'raw'
	key_list = tuple(['idx', 'delay', 'hum_in', 'temp_in', 'hum_out', 'temp_out', 'abs_pressure', 'wind_ave', 'wind_gust', 'wind_dir', 'rain', 'status', 'illuminance', 'uv'])
	conv = {'idx' : 'WSDateTime',  'delay' : 'WSInt',  'hum_in' : 'WSInt',  'temp_in' : 'WSFloat',  'hum_out' : 'WSInt',  'temp_out' : 'WSFloat',  'abs_pressure' : 'WSFloat',  'wind_ave' : 'WSFloat',  'wind_gust' : 'WSFloat',  'wind_dir' : 'WSInt',  'rain' : 'WSFloat',  'status' : 'WSStatus',  'illuminance' : 'WSFloat',  'uv' : 'WSInt'}


class CalibStore(CoreStore):
	'''Stores 'calibrated' weather station data.'''
	table = 'calib'
	key_list = tuple(['idx', 'delay', 'hum_in', 'temp_in', 'hum_out', 'temp_out', 'abs_pressure', 'rel_pressure', 'wind_ave', 'wind_gust', 'wind_dir', 'rain', 'status', 'illuminance', 'uv'])
	conv = {'idx' : 'WSDateTime', 'delay' : 'WSInt', 'hum_in' : 'WSInt', 'temp_in' : 'WSFloat', 'hum_out' : 'WSInt', 'temp_out' : 'WSFloat', 'abs_pressure' : 'WSFloat', 'rel_pressure' : 'WSFloat', 'wind_ave' : 'WSFloat', 'wind_gust' : 'WSFloat', 'wind_dir' : 'WSFloat', 'rain' : 'WSFloat', 'status' : 'WSStatus', 'illuminance' : 'WSFloat', 'uv' : 'WSInt'}


class HourlyStore(CoreStore):
	'''Stores hourly summary weather station data.'''
	table = 'hourly'
	key_list = tuple(['idx', 'hum_in', 'temp_in', 'hum_out', 'temp_out', 'abs_pressure', 'rel_pressure', 'pressure_trend', 'wind_ave', 'wind_gust', 'wind_dir', 'rain', 'illuminance', 'uv'])
	conv = {'idx' : 'WSDateTime', 'hum_in' : 'WSInt', 'temp_in' : 'WSFloat', 'hum_out' : 'WSInt', 'temp_out' : 'WSFloat', 'abs_pressure' : 'WSFloat', 'rel_pressure' : 'WSFloat', 'pressure_trend' : 'WSFloat', 'wind_ave' : 'WSFloat', 'wind_gust' : 'WSFloat', 'wind_dir' : 'WSFloat', 'rain' : 'WSFloat', 'illuminance' : 'WSFloat', 'uv' : 'WSInt'}


class DailyStore(CoreStore):
	'''Stores daily summary weather station data.'''
	table = 'daily'
	key_list = tuple(['idx', 'start', 'hum_out_ave', 'hum_out_min', 'hum_out_min_t', 'hum_out_max', 'hum_out_max_t', 'temp_out_ave', 'temp_out_min', 'temp_out_min_t', 'temp_out_max', 'temp_out_max_t', 'hum_in_ave', 'hum_in_min', 'hum_in_min_t', 'hum_in_max', 'hum_in_max_t', 'temp_in_ave', 'temp_in_min', 'temp_in_min_t', 'temp_in_max', 'temp_in_max_t', 'abs_pressure_ave', 'abs_pressure_min', 'abs_pressure_min_t', 'abs_pressure_max', 'abs_pressure_max_t', 'rel_pressure_ave', 'rel_pressure_min', 'rel_pressure_min_t', 'rel_pressure_max', 'rel_pressure_max_t', 'wind_ave', 'wind_gust', 'wind_gust_t', 'wind_dir', 'rain', 'illuminance_ave', 'illuminance_max', 'illuminance_max_t', 'uv_ave', 'uv_max', 'uv_max_t'])
	conv = {'idx' : 'WSDateTime', 'start' : 'WSDateTime', 'hum_out_ave' : 'WSFloat', 'hum_out_min' : 'WSInt', 'hum_out_min_t' : 'WSDateTime', 'hum_out_max' : 'WSInt', 'hum_out_max_t' : 'WSDateTime', 'temp_out_ave' : 'WSFloat', 'temp_out_min' : 'WSFloat', 'temp_out_min_t' : 'WSDateTime', 'temp_out_max' : 'WSFloat', 'temp_out_max_t' : 'WSDateTime', 'hum_in_ave' : 'WSFloat', 'hum_in_min' : 'WSInt', 'hum_in_min_t' : 'WSDateTime', 'hum_in_max' : 'WSInt', 'hum_in_max_t' : 'WSDateTime', 'temp_in_ave' : 'WSFloat', 'temp_in_min' : 'WSFloat', 'temp_in_min_t' : 'WSDateTime', 'temp_in_max' : 'WSFloat', 'temp_in_max_t' : 'WSDateTime', 'abs_pressure_ave' : 'WSFloat', 'abs_pressure_min' : 'WSFloat', 'abs_pressure_min_t' : 'WSDateTime', 'abs_pressure_max' : 'WSFloat', 'abs_pressure_max_t' : 'WSDateTime', 'rel_pressure_ave' : 'WSFloat', 'rel_pressure_min' : 'WSFloat', 'rel_pressure_min_t' : 'WSDateTime', 'rel_pressure_max' : 'WSFloat', 'rel_pressure_max_t' : 'WSDateTime', 'wind_ave' : 'WSFloat', 'wind_gust' : 'WSFloat', 'wind_gust_t' : 'WSDateTime', 'wind_dir' : 'WSFloat', 'rain' : 'WSFloat', 'illuminance_ave' : 'WSFloat', 'illuminance_max' : 'WSFloat', 'illuminance_max_t' : 'WSDateTime', 'uv_ave' : 'WSFloat', 'uv_max' : 'WSInt', 'uv_max_t' : 'WSDateTime'}


class MonthlyStore(CoreStore):
	'''Stores monthly summary weather station data.'''
	table = 'monthly'
	key_list = tuple(['idx', 'start', 'hum_out_ave', 'hum_out_min', 'hum_out_min_t', 'hum_out_max', 'hum_out_max_t', 'temp_out_ave', 'temp_out_min_lo', 'temp_out_min_lo_t', 'temp_out_min_hi', 'temp_out_min_hi_t', 'temp_out_min_ave', 'temp_out_max_lo', 'temp_out_max_lo_t', 'temp_out_max_hi', 'temp_out_max_hi_t', 'temp_out_max_ave', 'hum_in_ave', 'hum_in_min', 'hum_in_min_t', 'hum_in_max', 'hum_in_max_t', 'temp_in_ave', 'temp_in_min_lo', 'temp_in_min_lo_t', 'temp_in_min_hi', 'temp_in_min_hi_t', 'temp_in_min_ave', 'temp_in_max_lo', 'temp_in_max_lo_t', 'temp_in_max_hi', 'temp_in_max_hi_t', 'temp_in_max_ave', 'abs_pressure_ave', 'abs_pressure_min', 'abs_pressure_min_t', 'abs_pressure_max', 'abs_pressure_max_t', 'rel_pressure_ave', 'rel_pressure_min', 'rel_pressure_min_t', 'rel_pressure_max', 'rel_pressure_max_t', 'wind_ave', 'wind_gust', 'wind_gust_t', 'wind_dir', 'rain', 'rain_days', 'illuminance_ave', 'illuminance_max_lo', 'illuminance_max_lo_t', 'illuminance_max_hi', 'illuminance_max_hi_t', 'illuminance_max_ave', 'uv_ave', 'uv_max_lo', 'uv_max_lo_t', 'uv_max_hi', 'uv_max_hi_t', 'uv_max_ave'])
	conv = {'idx' : 'WSDateTime', 'start' : 'WSDateTime', 'hum_out_ave' : 'WSFloat', 'hum_out_min' : 'WSInt', 'hum_out_min_t' : 'WSDateTime', 'hum_out_max' : 'WSInt', 'hum_out_max_t' : 'WSDateTime', 'temp_out_ave' : 'WSFloat', 'temp_out_min_lo' : 'WSFloat', 'temp_out_min_lo_t' : 'WSDateTime', 'temp_out_min_hi' : 'WSFloat', 'temp_out_min_hi_t' : 'WSDateTime', 'temp_out_min_ave' : 'WSFloat', 'temp_out_max_lo' : 'WSFloat', 'temp_out_max_lo_t' : 'WSDateTime', 'temp_out_max_hi' : 'WSFloat', 'temp_out_max_hi_t' : 'WSDateTime', 'temp_out_max_ave' : 'WSFloat', 'hum_in_ave' : 'WSFloat', 'hum_in_min' : 'WSInt', 'hum_in_min_t' : 'WSDateTime', 'hum_in_max' : 'WSInt', 'hum_in_max_t' : 'WSDateTime', 'temp_in_ave' : 'WSFloat', 'temp_in_min_lo' : 'WSFloat', 'temp_in_min_lo_t' : 'WSDateTime', 'temp_in_min_hi' : 'WSFloat', 'temp_in_min_hi_t' : 'WSDateTime', 'temp_in_min_ave' : 'WSFloat', 'temp_in_max_lo' : 'WSFloat', 'temp_in_max_lo_t' : 'WSDateTime', 'temp_in_max_hi' : 'WSFloat', 'temp_in_max_hi_t' : 'WSDateTime', 'temp_in_max_ave' : 'WSFloat', 'abs_pressure_ave' : 'WSFloat', 'abs_pressure_min' : 'WSFloat', 'abs_pressure_min_t' : 'WSDateTime', 'abs_pressure_max' : 'WSFloat', 'abs_pressure_max_t' : 'WSDateTime', 'rel_pressure_ave' : 'WSFloat', 'rel_pressure_min' : 'WSFloat', 'rel_pressure_min_t' : 'WSDateTime', 'rel_pressure_max' : 'WSFloat', 'rel_pressure_max_t' : 'WSDateTime', 'wind_ave' : 'WSFloat', 'wind_gust' : 'WSFloat', 'wind_gust_t' : 'WSDateTime', 'wind_dir' : 'WSFloat', 'rain' : 'WSFloat', 'rain_days' : 'WSInt', 'illuminance_ave' : 'WSFloat', 'illuminance_max_lo' : 'WSFloat', 'illuminance_max_lo_t' : 'WSDateTime', 'illuminance_max_hi' : 'WSFloat', 'illuminance_max_hi_t' : 'WSDateTime', 'illuminance_max_ave' : 'WSFloat', 'uv_ave' : 'WSFloat', 'uv_max_lo' : 'WSInt', 'uv_max_lo_t' : 'WSDateTime', 'uv_max_hi' : 'WSInt', 'uv_max_hi_t' : 'WSDateTime', 'uv_max_ave' : 'WSFloat'}

