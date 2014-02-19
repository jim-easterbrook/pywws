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
  -p file or --pid file  write PID to file and go into the background
 data_dir is the root directory of the weather data (e.g. /data/weather)
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

from datetime import datetime, timedelta
import daemon
import getopt
import logging
import os
import PidFile
import sys
import time

from pywws import DataStore
from pywws import Localisation
from pywws.LogData import DataLogger
from pywws.Logger import ApplicationLogger
from pywws import Process
from pywws import Tasks

def LiveLog(data_dir):
    logger = logging.getLogger('pywws.LiveLog')
    params = DataStore.params(data_dir)
    status = DataStore.status(data_dir)
    # localise application
    Localisation.SetApplicationLanguage(params)
    # open data file stores
    raw_data = DataStore.data_store(data_dir)
    calib_data = DataStore.calib_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    # create a DataLogger object
    datalogger = DataLogger(params, status, raw_data)
    # create a RegularTasks object
    asynch = eval(params.get('config', 'asynchronous', 'False'))
    tasks = Tasks.RegularTasks(params, status, raw_data, calib_data,
                               hourly_data, daily_data, monthly_data,
                               asynch=asynch)
    # get live data
    try:
        for data, logged in datalogger.live_data(
                                    logged_only=(not tasks.has_live_tasks())):
            if logged:
                # process new data
                Process.Process(params, raw_data, calib_data,
                                hourly_data, daily_data, monthly_data)
                # do tasks
                tasks.do_tasks()
            else:
                tasks.do_live(data)
    except Exception, ex:
        logger.exception(ex)
    finally:
        tasks.stop_thread()
    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hl:p:v", ['help', 'log=', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    logfile = None
    pidfile = None
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
            return 0
        elif o in ('-l', '--log'):
            logfile = a
        elif o in ('-v', '--verbose'):
            verbose += 1
        elif o in ('-p', '--pid'):
            pidfile = a
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    if pidfile != None:
        with daemon.DaemonContext(pidfile = PidFile.PidFile(pidfile)):
            logger = ApplicationLogger(verbose, logfile)
            rtn = LiveLog(args[0])
    else:
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
