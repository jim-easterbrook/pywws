#!/usr/bin/env python

__usage__ = """
Remove rain offset from raw data.
 usage: %s [options] data_dir
 options are:
  -h or --help     display this help
 data_dir is the root directory of the weather data (e.g. $(HOME)/weather/data)
""" % __file__

from datetime import datetime
import getopt
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from pywws import DataStore

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __usage__.strip()
            return 0
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    data_dir = args[0]
    # date & time range of data to be changed, in UTC!
    start = datetime(2013, 10, 26, 15, 23)
    stop  = datetime(2013, 10, 30, 12, 47)
    # open data store
    raw_data = DataStore.data_store(data_dir)
    # change the data
    for data in raw_data[start:stop]:
        data['rain'] -= 263.1
        raw_data[data['idx']] = data
    # make sure it's saved
    raw_data.flush()
    # clear calibrated data that needs to be regenerated
    calib_data = DataStore.calib_store(data_dir)
    del calib_data[start:]
    calib_data.flush()
    # done
    return 0

if __name__ == "__main__":
    sys.exit(main())
