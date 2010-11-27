#!/usr/bin/env python

"""Get weather data, process it, prepare graphs & text files and
upload to a web site.

Typically run every hour from cron.
Comment out or remove the bits you don't need.

usage: python Hourly.py [options] [data_dir]
options are:
\t-h or --help\t\tdisplay this help
\t-v or --verbose\t\tincrease amount of reassuring messages
data_dir is the root directory of the weather data (default /data/weather)
"""

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
    # open data file stores
    raw_data = DataStore.data_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    # create a translation object for our locale
    translation = Localisation.GetTranslation(params)
    # get weather station data
    LogData.LogData(params, raw_data)
    # do the processing
    Process.Process(params, raw_data, hourly_data, daily_data, monthly_data)
    # do tasks
    if not Tasks.RegularTasks(
        params, raw_data, hourly_data, daily_data, monthly_data, translation
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
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) > 1:
        print >>sys.stderr, 'Error: 0 or 1 arguments required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    elif len(args) == 1:
        data_dir = args[0]
    else:
        data_dir = '/data/weather'
    logger = ApplicationLogger(verbose)
    return Hourly(data_dir)
if __name__ == "__main__":
    sys.exit(main())
