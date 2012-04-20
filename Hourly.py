#!/usr/bin/env python

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

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python Hourly.py [options] data_dir
 options are:
  -h or --help     display this help
  -v or --verbose  increase amount of reassuring messages
 data_dir is the root directory of the weather data (e.g. $(HOME)/weather/data)
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import os
import sys

from pywws import DataStore
from pywws import Localisation
from pywws import LogData
from pywws.Logger import ApplicationLogger
from pywws import Process
from pywws import Tasks

def Hourly(data_dir):
    # get file locations
    params = DataStore.params(data_dir)
    # localise application
    Localisation.SetApplicationLanguage(params)
    # open data file stores
    raw_data = DataStore.data_store(data_dir)
    calib_data = DataStore.calib_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    # get weather station data
    LogData.LogData(params, raw_data)
    # do the processing
    Process.Process(
        params, raw_data, calib_data, hourly_data, daily_data, monthly_data)
    # do tasks
    if not Tasks.RegularTasks(
        params, calib_data, hourly_data, daily_data, monthly_data
        ).do_tasks():
        return 1
    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __usage__.strip()
            return 0
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    return Hourly(args[0])

if __name__ == "__main__":
    sys.exit(main())
