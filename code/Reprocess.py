#!/usr/bin/env python

"""
Regenerate hourly and daily summary data.

usage: python Reprocess.py [options] data_dir
options are:
\t--help\t\t\tdisplay this help
data_dir is the root directory of the weather data
"""

import getopt
import os
import sys

from pywws import DataStore
from pywws.Logger import ApplicationLogger
from pywws import Process

def Reprocess(data_dir):
    # delete old format summary files
    print 'Deleting old summaries'
    for summary in ['calib', 'hourly', 'daily', 'monthly']:
        for root, dirs, files in os.walk(
                os.path.join(data_dir, summary), topdown=False):
            print root
            for file in files:
                os.unlink(os.path.join(root, file))
            os.rmdir(root)
    # create data summaries
    print 'Generating hourly and daily summaries'
    params = DataStore.params(data_dir)
    raw_data = DataStore.data_store(data_dir)
    calib_data = DataStore.calib_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    Process.Process(
        params, raw_data, calib_data, hourly_data, daily_data, monthly_data)
    return 0
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    for o, a in opts:
        if o == '--help':
            print __doc__.strip()
            return 0
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    logger = ApplicationLogger(1)
    data_dir = args[0]
    return Reprocess(data_dir)
if __name__ == "__main__":
    sys.exit(main())
