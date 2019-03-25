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

"""Store parameters in easy to access files, and access backend data

Introduction
------------

This module is at the core of pywws. By default it stores data on disc,
using a backend module which uses text files (see
:py:mod:`pywws.filedata`) but other plugin backend modules can be used
to use alternative means. These modules must adopt the same API (Class
names and methods) as :py:mod:`pywws.filedata` so as to be transparent
to the rest of pywws.

From a "user" point of view, the data is accessed as a cross between a
list and a dictionary. Each data record is indexed by a
:py:class:`datetime.datetime` object (dictionary behaviour), but
records are stored in order and can be accessed as slices (list
behaviour).

For example, to access the hourly data for Christmas day 2009, one
might do the following::

  from datetime import datetime
  import pywws.storage
  datastore = pywws.storage.PywwsContext('weather_data', False)
  hourly = datastore.hourly_data
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

See :py:mod:`pywws.filedata` for more details on the underlying data
store API.

Detailed API
------------

"""

from __future__ import with_statement

from ast import literal_eval
from contextlib import contextmanager
import logging
import os
import sys
import threading
import importlib

if sys.version_info[0] >= 3:
    from configparser import RawConfigParser
else:
    from ConfigParser import RawConfigParser

from pywws.weatherstation import WSDateTime
logger = logging.getLogger(__name__)


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

class PywwsContext(object):
    def __init__(self, data_dir, live_logging):
        self.live_logging = live_logging
        # open params and status files
        self.params = ParamStore(data_dir, 'weather.ini')
        self.status = ParamStore(data_dir, 'status.ini')
        # update weather.ini
        self.update_params()
        # create working directories
        self.work_dir = self.params.get('paths', 'work', '/tmp/pywws')
        self.output_dir = os.path.join(self.work_dir, 'output')
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)
        # Load whichever data store module was specified,
        # Defaults to the original file store
        datastoretype = self.params.get('paths', 'datastoretype', 'filedata')
        DataStoreModule = importlib.import_module(
            '.'+datastoretype, package='pywws')
        # open data file stores
        self.raw_data = DataStoreModule.RawStore(data_dir)
        self.calib_data = DataStoreModule.CalibStore(data_dir)
        self.hourly_data = DataStoreModule.HourlyStore(data_dir)
        self.daily_data = DataStoreModule.DailyStore(data_dir)
        self.monthly_data = DataStoreModule.MonthlyStore(data_dir)
        # create an event to shutdown threads
        self.shutdown = threading.Event()

    def update_params(self):
        # convert day end hour
        day_end_str = self.params.get('config', 'day end hour')
        if day_end_str and not ',' in day_end_str:
            logger.error('updating "day end hour" in weather.ini')
            day_end_str += ', False'
            self.params.set('config', 'day end hour', day_end_str)
        # convert uploads to use pywws.service.{copy,ftp,sftp,twitter}
        local_site = self.params.get('ftp', 'local site')
        secure = self.params.get('ftp', 'secure')
        privkey = self.params.get('ftp', 'privkey')
        if local_site or secure or privkey:
            if local_site == 'True':
                self.params.set(
                    'copy', 'directory', self.params.get('ftp', 'directory', ''))
                mod = 'copy'
            elif secure == 'True':
                for key in ('site', 'user', 'directory', 'port',
                            'password', 'privkey'):
                    self.params.set('sftp', key, self.params.get('ftp', key, ''))
                mod = 'sftp'
            else:
                mod = 'ftp'
            for key in ('local site', 'secure', 'privkey'):
                self.params.unset('ftp', key)
            for section in self.params._config.sections():
                if section.split()[0] != 'cron' and section not in [
                        'live', 'logged', 'hourly', '12 hourly', 'daily']:
                    continue
                for t_p in ('text', 'plot'):
                    templates = literal_eval(
                        self.params.get(section, t_p, '[]'))
                    services = literal_eval(
                        self.params.get(section, 'services', '[]'))
                    changed = False
                    for n, template in enumerate(templates):
                        if isinstance(template, (list, tuple)):
                            template, flags = template
                            templates[n] = template
                            changed = True
                        else:
                            flags = ''
                        if t_p == 'plot':
                            result = os.path.splitext(template)[0]
                        else:
                            result = template
                        if 'L' in flags:
                            task = None
                        elif 'T' in flags:
                            task = ('twitter', result)
                        else:
                            task = (mod, result)
                        if task and task not in services:
                            services.append(task)
                            changed = True
                    if changed:
                        logger.error('updating %s in [%s]', t_p, section)
                        self.params.set(section, t_p, repr(templates))
                        self.params.set(section, 'services', repr(services))
        self.params.unset('config', 'config version')

    def terminate(self):
        if self.live_logging:
            # signal threads to terminate
            self.shutdown.set()
        # wait for threads to terminate
        for thread in threading.enumerate():
            if thread == threading.current_thread():
                continue
            logger.debug('waiting for thread ' + thread.name)
            thread.join()

    def flush(self):
        logger.debug('flushing')
        self.params.flush()
        self.status.flush()
        self.raw_data.flush()
        self.calib_data.flush()
        self.hourly_data.flush()
        self.daily_data.flush()
        self.monthly_data.flush()


@contextmanager
def pywws_context(data_dir, live_logging=False):
    ctx = PywwsContext(data_dir, live_logging)
    try:
        yield ctx
    finally:
        ctx.terminate()
        ctx.flush()
