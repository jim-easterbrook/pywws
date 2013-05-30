#!/usr/bin/env python

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

"""Get weather data, store it, and process it.

Run this continuously, having set what tasks are to be done. ::

%s

For more information on using ``LiveLog.py``, see
:doc:`../guides/livelogging`.

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.LiveLog [options] data_dir
 options are:
  -h      or --help      display this help
  -l file or --log file  write log information to file
  -v      or --verbose   increase amount of reassuring messages
 data_dir is the root directory of the weather data (e.g. /data/weather)
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

from datetime import datetime, timedelta
import getopt
import logging
import os
import sys
import time

from pywws import DataStore
from pywws import Localisation
from pywws.LogData import Catchup, CheckFixedBlock
from pywws.Logger import ApplicationLogger
from pywws import Process
from pywws import Tasks
from pywws import WeatherStation

def LiveLog(data_dir):
    logger = logging.getLogger('pywws.LiveLog')
    params = DataStore.params(data_dir)
    status = DataStore.status(data_dir)
    # localise application
    Localisation.SetApplicationLanguage(params)
    # connect to weather station
    ws_type = params.get('fixed', 'ws type')
    if ws_type:
        params.unset('fixed', 'ws type')
        params.set('config', 'ws type', ws_type)
    ws_type = params.get('config', 'ws type', '1080')
    ws = WeatherStation.weather_station(
        ws_type=ws_type, params=params, status=status)
    fixed_block = CheckFixedBlock(ws, params, status, logger)
    if not fixed_block:
        logger.error("Invalid data from weather station")
        return 3
    # open data file stores
    raw_data = DataStore.data_store(data_dir)
    calib_data = DataStore.calib_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    # create a RegularTasks object
    tasks = Tasks.RegularTasks(
        params, status, calib_data, hourly_data, daily_data, monthly_data)
    # get time of last logged data
    two_minutes = timedelta(minutes=2)
    last_stored = raw_data.before(datetime.max)
    if last_stored == None:
        last_stored = datetime.min
    if datetime.utcnow() < last_stored:
        raise ValueError('Computer time is earlier than last stored data')
    last_stored += two_minutes
    # get live data
    hour = timedelta(hours=1)
    next_hour = datetime.utcnow().replace(
                                    minute=0, second=0, microsecond=0) + hour
    next_ptr = None
    for data, ptr, logged in ws.live_data(
                                    logged_only=(not tasks.has_live_tasks())):
        now = data['idx']
        if logged:
            if ptr == next_ptr:
                # data is contiguous with last logged value
                raw_data[now] = data
            else:
                # catch up missing data
                Catchup(ws, logger, raw_data, now, ptr)
            next_ptr = ws.inc_ptr(ptr)
            # process new data
            Process.Process(params, status, raw_data, calib_data,
                            hourly_data, daily_data, monthly_data)
            # do tasks
            tasks.do_tasks()
            if now >= next_hour:
                next_hour += hour
                fixed_block = CheckFixedBlock(ws, params, status, logger)
                if not fixed_block:
                    logger.error("Invalid data from weather station")
                    return 3
                # save any unsaved data
                raw_data.flush()
        else:
            tasks.do_live(data)
    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hl:v", ['help', 'log=', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    logfile = None
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
            return 0
        elif o in ('-l', '--log'):
            logfile = a
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    logger = ApplicationLogger(verbose, logfile)
    return LiveLog(args[0])

if __name__ == "__main__":
    logger = logging.getLogger('pywws')
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
    except Exception, e:
        logger.exception(str(e))
