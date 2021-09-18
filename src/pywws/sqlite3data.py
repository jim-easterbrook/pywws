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

It should also be possible for this module to form the basis of a
full client-server based SQL module using, for example, MySQL etc.

The Python builtin sqlite3 module is used which has a threadsafety of 1,
therefore this module creates a connection with every Store (sub)class
instance. This however brings concurrancy issues and so this module makes
use of the underlying sqlite3's Write-Ahead-Loging and Shared Cache modes
to relieve this. These rely on up to date sqlite3 libraries and may not
work on older networked drives which do not support the right locking
semantics required by sqlite3.


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
  hourly = pywws.filedata.HourlyStore("weather_data")
  for data in hourly[datetime(2009, 12, 25):datetime(2009, 12, 26)]:
    print(data["idx"], data["temp_out"])

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
from datetime import date, datetime, timedelta

import pytz

from pywws.weatherstation import WSDateTime, WSFloat, WSInt, WSStatus

# Data type adapt: Python ==> SQLite3
def _adapt_WSDateTime(dt):
    """Return unix timestamp of the datetime like input.
    If conversion overflows high, return sint64_max ,
    if underflows, return 0
    """
    try:
        ts = int(
            (dt.replace(tzinfo=pytz.utc)
            - datetime(1970,1,1,tzinfo=pytz.utc)
            ).total_seconds()
        )
    except (OverflowError,OSError):
        if dt < datetime.now():
            ts = 0
        else:
            ts = 2**63-1
    return ts

def _adapt_WSStatus(status):
    """Return integer representing WSStatus dictionary input"""
    return int(WSStatus.to_csv(status))

# Data type convert SQLite3 ==> Python
def _convert_WSDateTime(b):
    """Return a WSDateTime object for a given unix timestamp"""
    return WSDateTime.utcfromtimestamp(int(b))

def _convert_WSStatus(b):
    """Return a WSStatus dictionary for a given number"""
    return WSStatus.from_csv(b)

def _convert_WSFloat(b):
    """Return a WSFloat for the given input"""
    return WSFloat(b)

def _convert_WSInt(b):
    """Return WSInt for the given input"""
    return WSInt(b)

sqlite3.enable_shared_cache(True)

sqlite3.register_adapter(datetime, _adapt_WSDateTime)
sqlite3.register_adapter(WSDateTime, _adapt_WSDateTime)
sqlite3.register_adapter(WSStatus, _adapt_WSStatus)
# Ensures SQLite handles these special types and treats them as standard float
sqlite3.register_adapter(WSFloat, float)
# Wnsures SQLite handles these special types and treats them as standard int
sqlite3.register_adapter(WSInt, int)

sqlite3.register_converter("WSDateTime", _convert_WSDateTime)
sqlite3.register_converter("WSStatus", _convert_WSStatus)
sqlite3.register_converter("WSFloat", _convert_WSFloat)
sqlite3.register_converter("WSInt", _convert_WSInt)


class CoreStore(object):
    """Provides a dictionary/list like interface
    to an underlying SQLite3 database
    """
    # Overrides type conversion based on incorrect sql type
    # (i.e. for the primary key)
    conv = {"idx":None}
    key_list = tuple(conv.keys())
    table = ""
    _keycol = "idx"
    if len(conv) == 0:
        raise KeyError("No columns are defined.")
    if _keycol not in key_list:
        # Check that the key column is present
        raise KeyError(
            "Key column '{}' is not in the key list".format(keycol)
        )

    def __init__(self, dir_name):
        key_list = self.key_list
        conv = self.conv
        table = self.table
        keycol = self._keycol
        dbpath = os.path.abspath(os.path.join(dir_name, "pywws.db"))
        self._connection = sqlite3.connect(
            dbpath,
            detect_types=sqlite3.PARSE_COLNAMES
        )
        self._connection.row_factory = sqlite3.Row
        con = self._connection

        if con.execute(
            "PRAGMA journal_mode=WAL"
        ).fetchone()["journal_mode"] != "wal":
            raise TypeError("Database is not in Write-Ahead-Log mode")
        # Create the table if its not already there.
        # Assume all data fields are NUM so that SQLite can optimise storage
        # as it will choose the smallest integer representation between 8-64bit,
        # while floats are always 64bit. Set idx as a unique integer primary
        # key so searches are faster, storage requirements smaller,
        # the rowid column is eliminated so there is no need for secondary
        # indices. Suitable converters/adapters are then applied.
        if con.execute(
            """SELECT COUNT(*) FROM sqlite_master
            WHERE type="table" AND name=?;""",
            (table,)
        ).fetchone()[0] == 0:
            con.executescript(
                """CREATE TABLE IF NOT EXISTS {table} (
                {keycol} INTEGER PRIMARY KEY, {columns} );""".format(
                    table=table,
                    keycol=keycol,
                    columns=", ".join(
                        "{} NUM".format(key)
                        for key in conv
                        if key != keycol
                    )
                )
            )

        # Get all columns from the database
        sql_key_list = tuple(
            (row["name"],row["pk"])
            for row in con.execute(
                "SELECT name, pk FROM PRAGMA_TABLE_INFO(?);",
                (table,)
            )
        )

        # Fetch the primary key - check there is only one
        sql_pk = tuple(key[0] for key in sql_key_list if key[1] == 1)
        if len(sql_pk) != 1 or sql_pk[0] != keycol:
            raise KeyError(
                "Mismatch between database primary key and what was expected"
            )

        # Convert this to just a set of keys
        sql_key_list = set(key[0] for key in sql_key_list)
        # Check that no columns are missing
        if not set(conv.keys()) <= sql_key_list:
            raise KeyError(
                "Mismatch between database columns and what was expected"
            )

        # SQL snippet which casts all columns to the correct data types
        # for SELECT * type queries
        self.selallcols = ", ".join(
            '{col} AS "{col} [{conv}]"'.format(
                col=col,
                conv=conv[col]
            ) for col in key_list
        )
        # SQL snippet which casts the key column to the correct data type
        # for SELECT {keycol} type queries
        self.selkeycol = '{keycol} AS "{keycol} [{conv}]"'.format(
            keycol=keycol,
            conv=conv[keycol]
        )

    def __del__(self):
        """Prior to object being deleted, update SQLite statistics,
        then close connection gracefully
        """
        with self._connection as con:
            con.executescript(
                """ANALYZE {}; PRAGMA wal_checkpoint(TRUNCATE);
                """.format(self.table)
            )
        self._connection.close()

    def __len__(self):
        """Return the exact number of records in the table"""
        # Direct count of all records - could be slow.
        return self._connection.execute(
            "SELECT COUNT(*) FROM {};".format(self.table)
        ).fetchone()[0]
    
    def __length_hint__(self):
        """Return the approximate table size based on internal database
        statistics if present, otherwise, find the actual length
        """
        # Assuming the database has been analyzed before, the stat1 table
        # should contain the total row count for the table as the first number
        # in the stat column from when it was last analyzed. Very fast but may
        # not be up to date
        try:
            return int(self._connection.execute(
                "SELECT stat FROM sqlite_stat1 WHERE tbl=?;",
                (self.table,)
                ).fetchone()[0].split(' ')[0]
            )
        except (TypeError,sqlite3.OperationalError):
            return self.__len__()

    def _predicate(self, i):
        """Given a valid datetime or slace, return the predicate portion
        of the SQL query, a boolean indicating whether multiple items are
        expected from the result, and a dictionary of parameters for the query
        """
        if isinstance(i, slice):
            if i.step is not None:
                raise TypeError("Slice step not permitted")
            if ( (i.start is not None and not isinstance(i.start, datetime))
                or (i.stop is not None and not isinstance(i.stop, datetime))
            ):
                raise TypeError(
                    "Slice indices must be {} or None".format(datetime)
                )
            if i.start is not None and i.stop is not None:
                if i.start > i.stop:
                    raise ValueError(
                        "Start index is greater than the End index"
                    )
                else:
                    # Substitution of the key column, but the
                    # parameters themselves will be substituted by sqlite3
                    predicate = "WHERE {} BETWEEN :start AND :stop".format(
                        self._keycol
                    )
            elif i.start is not None:
                # i.stop will also be None
                predicate = "WHERE {} >= :start".format(self._keycol)
            elif i.stop is not None:
                # i.start will also be None
                predicate = "WHERE {} <= :stop".format(self._keycol)
            else:
                # both are None, so equivalent to wanting everything
                predicate = ""
            multi = True
            pred = {"start": i.start, "stop": i.stop}
        elif isinstance(i, datetime):
            # Substitution of the key column, but the
            # parameters themselves will be substituted by sqlite3
            predicate = "WHERE {} = :key".format(self._keycol)
            multi = False
            pred = {"key": i}
        else:
            # not a slice or a datetime object
            raise TypeError("List indices must be {}".format(datetime))
        # predicate is the end of the query string.
        # multi is a boolean indicating whether the result should be iterable
        # or not. pred is a dict of the parameters for substitution
        return (predicate, multi, pred)

    def __getitem__(self, i):
        """Return the data item or items with index i.
        
        i must be a datetime object or a slice. If i is a single datetime
        then a value with that index must exist.
        """
        predicate, multi, params = self._predicate(i)
        results = self._connection.execute(
            "SELECT {} FROM {} {};".format(
                self.selallcols,self.table,predicate), params)
        if multi:#
            # If multiple items are expected, give a generator
            return (dict(row) for row in results)
        else:
            # If one item is expected, return it directly
            item = results.fetchone()
            return self.__missing__(i) if item is None else dict(item)

    def __contains__(self, i):
        """Return True if i is in the table, else False"""
        if self._connection.execute(
            "SELECT count(*) FROM {} WHERE {} = ?;".format(
                self.table,
                self._keycol
            ),(i,)).fetchone()[0] > 0:
            return True
        else:
            return False

    def __missing__(self, i):
        raise IndexError(i)

    def __setitem__(self, i, x):
        """Store a value x with index i.
        
        i must be a datetime object. If there is already a value with
        index i, it is overwritten.
        """
        if not isinstance(i, datetime):
            raise TypeError("'{}' is not a datetime object".format(i))
        elif not isinstance(x, dict):
            raise TypeError("Values not a dictionary")
        x[self._keycol] = i
        with self._connection as con:
            con.execute(
                """INSERT OR REPLACE INTO {table} ({keylist})
                VALUES (:{vallist});
                """.format(
                    table=self.table,
                    keylist=", ".join(x),
                    vallist=", :".join(x)
                ), x)

    def update(self, i):
        """D.update(E) -> None.  Update D from iterable E with pre-existing
        items being overwritten.
        
        Elements in E are assumed to be dicts containing the primary key to
        allow the equivalent of:
        for k in E: D[k.primary_key] = k
        """
        key_list = self.key_list
        keynone = {key:None for key in key_list}
        # Generator which fills in missing data from the original iterator
        def datagen(i):
            for datum in i:
                tmp = keynone.copy()
                tmp.update(datum)
                yield tmp
        with self._connection as con:
            con.executemany(
                """INSERT OR REPLACE INTO {table} ({keylist})
                VALUES (:{vallist});
                """.format(table=self.table,
                    keylist=", ".join(self.key_list),
                    vallist=", :".join(self.key_list)
                ), datagen(i))

    def __delitem__(self, i):
        """Delete the data item or items with index i.
        
        i must be a datetime object or a slice. If i is a single datetime
        then a value with that index must exist.
        """
        predicate, multi, params = self._predicate(i)
        with self._connection as con:
            if con.execute("DELETE FROM {} {};".format(
                self.table,
                predicate
            ), params).rowcount == 0 and multi is False:
                raise KeyError(i)

    def before(self, i):
        """Return datetime of newest existing data record whose datetime
        is < idx. If no such record exists, return None.
        """
        if not isinstance(i, datetime):
            raise TypeError("'{}' is not a datetime object".format(i))
        else:
            result = self._connection.execute(
                """SELECT {selkeycol} FROM {table} WHERE
                {keycol} < :key ORDER BY {keycol} DESC LIMIT 1;
                """.format(
                    selkeycol=self.selkeycol,
                    table=self.table,
                    keycol=self._keycol
                ), {"key":i}).fetchone()
        return result[self._keycol] if result is not None else None

    def after(self, i):
        """Return datetime of oldest existing data record whose datetime
        is >= idx. If no such record exists, return None.
        """
        if not isinstance(i, datetime):
            raise TypeError("'{}' is not a datetime object".format(i))
        else:
            result = self._connection.execute(
                """SELECT {selkeycol} FROM {table} WHERE
                {keycol} >= :key ORDER BY {keycol} ASC LIMIT 1;""".format(
                    selkeycol=self.selkeycol,
                    table=self.table,
                    keycol=self._keycol
                ), {"key":i}).fetchone()
        return result[self._keycol] if result is not None else None

    def nearest(self, i):
        """Return datetime of record whose datetime is nearest idx."""
        if not isinstance(i, datetime):
            raise TypeError("'{}' is not a datetime object".format(i))
        else:
            result = self._connection.execute(
                """SELECT {selkeycol} FROM {table} ORDER BY
                ABS({keycol}-:key) ASC LIMIT 1;""".format(
                    selkeycol=self.selkeycol,
                    table=self.table,
                    keycol=self._keycol
                ), {"key":i}).fetchone()
        return result[self._keycol] if result is not None else None

    def flush(self):
        """Commits any uncommitted data and then flushes the write ahead log"""
        with self._connection as con:
            # execute script has implied commit before it
            con.executescript("PRAGMA wal_checkpoint(TRUNCATE);")

    def keys(self):
        """D.keys() -> a set-like object providing a view on D's keys"""
        return set(
            row[self._keycol] for row in self._connection.execute(
                """SELECT DISTINCT {} FROM {} ORDER BY {} ASC;""".format(
                    self.selkeycol,
                    self.table,
                    self._keycol
                )
            )
        )

    def __iter__(self):
        """Iterates over all rows in ascending order of key column"""
        for row in self._connection.execute(
            """SELECT {} FROM {} ORDER BY {} ASC;""".format(
                self.selallcols,
                self.table,
                self._keycol
            )
        ):
            yield dict(row)

    def __reversed__(self):
        """Iterates over all rows in decending order of key column"""
        for row in self._connection.execute(
            """SELECT {} FROM {} ORDER BY {} DESC;""".format(
                self.selallcols,
                self.table,
                self._keycol
            )
        ):
            yield dict(row)

    def values(self):
        """D.values() -> an object providing a view on D's values"""
        for item in self.__iter__():
            yield item

    def items(self):
        """D.items() -> a set-like object providing a view on D's items"""
        keycol = self._keycol
        for row in self.__iter__():
            yield (row[keycol], dict(row))

    def get(self, key, default=None):
        """D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None."""
        try:
            return self[key]
        except (KeyError, IndexError):
            return default

    def clear(self):
        """S.clear() -> None -- remove all items from S"""
        with self._connection as con:
            con.execute("DELETE FROM {};".format(self.table))

    def setdefault(self, key, default=None):
        """D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D"""
        try:
            return self[key]
        except (KeyError, IndexError):
            self[key] = default
        return default

    __marker = object()
    def pop(self, key, default=__marker):
        """D.pop(k[,d]) -> v
        
        Remove specified key and return the corresponding value.
        If key is not found, d is returned if given,
        otherwise KeyError is raised.
        """
        try:
            value = self[key]
            del self[key]
            return value
        except (KeyError, IndexError):
            if default is self.__marker:
                raise
            else:
                return default

    def popitem(self):
        """D.popitem() -> (k, v)
        
        Remove and return some (key, value) pair
        as a 2-tuple; but raise KeyError if D is empty.
        """
        try:
            value = next(iter(self))
            key = value[self._keycol]
        except StopIteration:
            raise KeyError
        del self[key]
        return key, value


class RawStore(CoreStore):
    """Stores raw weather station data."""
    table = "raw"
    conv = {
        "idx"          : "WSDateTime",
        "delay"        : "WSInt",
        "hum_in"       : "WSInt",
        "temp_in"      : "WSFloat",
        "hum_out"      : "WSInt",
        "temp_out"     : "WSFloat",
        "abs_pressure" : "WSFloat",
        "wind_ave"     : "WSFloat",
        "wind_gust"    : "WSFloat",
        "wind_dir"     : "WSInt",
        "rain"         : "WSFloat",
        "status"       : "WSStatus",
        "illuminance"  : "WSFloat",
        "uv"           : "WSInt"
    }
    key_list = tuple(conv.keys())


class CalibStore(CoreStore):
    """Stores "calibrated" weather station data."""
    table = "calib"
    conv = {
        "idx"          : "WSDateTime",
        "delay"        : "WSInt",
        "hum_in"       : "WSInt",
        "temp_in"      : "WSFloat",
        "hum_out"      : "WSInt",
        "temp_out"     : "WSFloat",
        "abs_pressure" : "WSFloat",
        "rel_pressure" : "WSFloat",
        "wind_ave"     : "WSFloat",
        "wind_gust"    : "WSFloat",
        "wind_dir"     : "WSFloat",
        "rain"         : "WSFloat",
        "status"       : "WSStatus",
        "illuminance"  : "WSFloat",
        "uv"           : "WSInt"
    }
    key_list = tuple(conv.keys())


class HourlyStore(CoreStore):
    """Stores hourly summary weather station data."""
    table = "hourly"
    conv = {
        "idx"            : "WSDateTime",
        "hum_in"         : "WSInt",
        "temp_in"        : "WSFloat",
        "hum_out"        : "WSInt",
        "temp_out"       : "WSFloat",
        "abs_pressure"   : "WSFloat",
        "rel_pressure"   : "WSFloat",
        "pressure_trend" : "WSFloat",
        "wind_ave"       : "WSFloat",
        "wind_gust"      : "WSFloat",
        "wind_dir"       : "WSFloat",
        "rain"           : "WSFloat",
        "illuminance"    : "WSFloat",
        "uv"             : "WSInt"
    }
    key_list = tuple(conv.keys())


class DailyStore(CoreStore):
    """Stores daily summary weather station data."""
    table = "daily"
    conv = {
        "idx"                : "WSDateTime",
        "start"              : "WSDateTime",
        "hum_out_ave"        : "WSFloat",
        "hum_out_min"        : "WSInt",
        "hum_out_min_t"      : "WSDateTime",
        "hum_out_max"        : "WSInt",
        "hum_out_max_t"      : "WSDateTime",
        "temp_out_ave"       : "WSFloat",
        "temp_out_min"       : "WSFloat",
        "temp_out_min_t"     : "WSDateTime",
        "temp_out_max"       : "WSFloat",
        "temp_out_max_t"     : "WSDateTime",
        "hum_in_ave"         : "WSFloat",
        "hum_in_min"         : "WSInt",
        "hum_in_min_t"       : "WSDateTime",
        "hum_in_max"         : "WSInt",
        "hum_in_max_t"       : "WSDateTime",
        "temp_in_ave"        : "WSFloat",
        "temp_in_min"        : "WSFloat",
        "temp_in_min_t"      : "WSDateTime",
        "temp_in_max"        : "WSFloat",
        "temp_in_max_t"      : "WSDateTime",
        "abs_pressure_ave"   : "WSFloat",
        "abs_pressure_min"   : "WSFloat",
        "abs_pressure_min_t" : "WSDateTime",
        "abs_pressure_max"   : "WSFloat",
        "abs_pressure_max_t" : "WSDateTime",
        "rel_pressure_ave"   : "WSFloat",
        "rel_pressure_min"   : "WSFloat",
        "rel_pressure_min_t" : "WSDateTime",
        "rel_pressure_max"   : "WSFloat",
        "rel_pressure_max_t" : "WSDateTime",
        "wind_ave"           : "WSFloat",
        "wind_gust"          : "WSFloat",
        "wind_gust_t"        : "WSDateTime",
        "wind_dir"           : "WSFloat",
        "rain"               : "WSFloat",
        "illuminance_ave"    : "WSFloat",
        "illuminance_max"    : "WSFloat",
        "illuminance_max_t"  : "WSDateTime",
        "uv_ave"             : "WSFloat",
        "uv_max"             : "WSInt",
        "uv_max_t"           : "WSDateTime"
    }
    key_list = tuple(conv.keys())


class MonthlyStore(CoreStore):
    """Stores monthly summary weather station data."""
    table = "monthly"
    conv = {
        "idx"                  : "WSDateTime",
        "start"                : "WSDateTime",
        "hum_out_ave"          : "WSFloat",
        "hum_out_min"          : "WSInt",
        "hum_out_min_t"        : "WSDateTime",
        "hum_out_max"          : "WSInt",
        "hum_out_max_t"        : "WSDateTime",
        "temp_out_ave"         : "WSFloat",
        "temp_out_min_lo"      : "WSFloat",
        "temp_out_min_lo_t"    : "WSDateTime",
        "temp_out_min_hi"      : "WSFloat",
        "temp_out_min_hi_t"    : "WSDateTime",
        "temp_out_min_ave"     : "WSFloat",
        "temp_out_max_lo"      : "WSFloat",
        "temp_out_max_lo_t"    : "WSDateTime",
        "temp_out_max_hi"      : "WSFloat",
        "temp_out_max_hi_t"    : "WSDateTime",
        "temp_out_max_ave"     : "WSFloat",
        "hum_in_ave"           : "WSFloat",
        "hum_in_min"           : "WSInt",
        "hum_in_min_t"         : "WSDateTime",
        "hum_in_max"           : "WSInt",
        "hum_in_max_t"         : "WSDateTime",
        "temp_in_ave"          : "WSFloat",
        "temp_in_min_lo"       : "WSFloat",
        "temp_in_min_lo_t"     : "WSDateTime",
        "temp_in_min_hi"       : "WSFloat",
        "temp_in_min_hi_t"     : "WSDateTime",
        "temp_in_min_ave"      : "WSFloat",
        "temp_in_max_lo"       : "WSFloat",
        "temp_in_max_lo_t"     : "WSDateTime",
        "temp_in_max_hi"       : "WSFloat",
        "temp_in_max_hi_t"     : "WSDateTime",
        "temp_in_max_ave"      : "WSFloat",
        "abs_pressure_ave"     : "WSFloat",
        "abs_pressure_min"     : "WSFloat",
        "abs_pressure_min_t"   : "WSDateTime",
        "abs_pressure_max"     : "WSFloat",
        "abs_pressure_max_t"   : "WSDateTime",
        "rel_pressure_ave"     : "WSFloat",
        "rel_pressure_min"     : "WSFloat",
        "rel_pressure_min_t"   : "WSDateTime",
        "rel_pressure_max"     : "WSFloat",
        "rel_pressure_max_t"   : "WSDateTime",
        "wind_ave"             : "WSFloat",
        "wind_gust"            : "WSFloat",
        "wind_gust_t"          : "WSDateTime",
        "wind_dir"             : "WSFloat",
        "rain"                 : "WSFloat",
        "rain_days"            : "WSInt",
        "illuminance_ave"      : "WSFloat",
        "illuminance_max_lo"   : "WSFloat",
        "illuminance_max_lo_t" : "WSDateTime",
        "illuminance_max_hi"   : "WSFloat",
        "illuminance_max_hi_t" : "WSDateTime",
        "illuminance_max_ave"  : "WSFloat",
        "uv_ave"               : "WSFloat",
        "uv_max_lo"            : "WSInt",
        "uv_max_lo_t"          : "WSDateTime",
        "uv_max_hi"            : "WSInt",
        "uv_max_hi_t"          : "WSDateTime",
        "uv_max_ave"           : "WSFloat"
    }
    key_list = tuple(conv.keys())
