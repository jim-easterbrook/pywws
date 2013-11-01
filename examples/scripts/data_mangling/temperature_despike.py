#!/usr/bin/env python

__usage__ = """
Remove temperature spikes from raw data.
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
from pywws.Process import SECOND

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
    start = datetime(2013, 10, 27, 11, 21)
    stop  = datetime(2013, 10, 29, 18, 32)
    # open data store
    raw_data = DataStore.data_store(data_dir)
    # preload array of nearby timestamps
    idx = raw_data.before(raw_data.before(start))
    local_times = []
    for i in range(5):
        local_times.append(idx)
        idx = raw_data.after(idx + SECOND)
    # change the data
    for data in raw_data[start:stop]:
        if data['temp_out'] is not None:
            # get temperatures at nearby times
            temp_list = []
            for ts in local_times:
                temp = raw_data[ts]['temp_out']
                if temp is not None:
                    temp_list.append(temp)
            # get median
            temp_list.sort()
            median = temp_list[len(temp_list) / 2]
            # remove anything too far from median
            if abs(data['temp_out'] - median) >= 2.0:
                print str(data['idx']), temp_list, data['temp_out']
                data['temp_out'] = None
                raw_data[data['idx']] = data
        # get next timestamp
        del local_times[0]
        local_times.append(idx)
        idx = raw_data.after(idx + SECOND)
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
