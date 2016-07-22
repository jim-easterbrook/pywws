#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-16  pywws contributors

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

"""Get weather data, process it, prepare graphs & text files and
upload to a web site.

Typically run every hour from cron. ::

%s

This script does little more than call other modules in sequence to
get data from the weather station, process it, plot some graphs,
generate some text files and upload the results to a web site.

For more information on using ``Hourly.py``, see
:doc:`../guides/hourlylogging`.

"""

from __future__ import absolute_import

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: %s [options] data_dir
 options are:
  -h or --help     display this help
  -v or --verbose  increase amount of reassuring messages
 data_dir is the root directory of the weather data (e.g. $(HOME)/weather/data)
"""
__doc__ %= __usage__ % ('python -m pywws.Hourly')

import getopt
import os
import sys

from pywws import DataStore
from pywws import Localisation
from pywws.LogData import DataLogger
from pywws.Logger import ApplicationLogger
from pywws import Process
from pywws import Tasks

def Hourly(data_dir):
    # get file locations
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
    # get weather station data
    DataLogger(params, status, raw_data).log_data()
    # do the processing
    Process.Process(params,
                    raw_data, calib_data, hourly_data, daily_data, monthly_data)
    # do tasks
    if not Tasks.RegularTasks(params, status, raw_data, calib_data,
                              hourly_data, daily_data, monthly_data).do_tasks():
        return 1
    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv
    usage = (__usage__ % (argv[0])).strip()
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, usage
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.split('\n\n')[0]
            print usage
            return 0
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, usage
        return 2
    logger = ApplicationLogger(verbose)
    return Hourly(args[0])

if __name__ == "__main__":
    sys.exit(main())
