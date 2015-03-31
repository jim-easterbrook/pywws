#!/usr/bin/env python

__usage__ = """
Remove temperature spikes from raw data.
 usage: %s [options] data_dir
 options are:
  -h or --help     display this help
  -n or --noaction show what would be done but don't modify data
 data_dir is the root directory of the weather data (e.g. $(HOME)/weather/data)
""" % __file__

from datetime import datetime, timedelta
import getopt
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from pywws import DataStore
from pywws.constants import SECOND

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hn", ['help', 'noaction'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    noaction = False
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __usage__.strip()
            return 0
        elif o == '-n' or o == '--noaction':
            noaction = True
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
    # process the data
    aperture = timedelta(minutes=14, seconds=30)
    # make list of changes to apply after examining the data
    changes = []
    for data in raw_data[start:stop]:
        if data['temp_out'] is None:
            continue
        # get temperatures at nearby times
        idx = data['idx']
        temp_list = []
        for local_data in raw_data[idx-aperture:idx+aperture]:
            temp = local_data['temp_out']
            if temp is not None:
                temp_list.append(temp)
        if len(temp_list) < 3:
            continue
        # get median
        temp_list.sort()
        median = temp_list[len(temp_list) / 2]
        # remove anything too far from median
        if abs(data['temp_out'] - median) >= 2.5:
            print str(idx), temp_list, data['temp_out']
            changed = dict(data)
            changed['temp_out'] = None
            changes.append(changed)
    # store the changed data
    if changes and not noaction:
        for changed in changes:
            raw_data[changed['idx']] = changed
        # make sure it's saved
        raw_data.flush()
        # clear calibrated data that needs to be regenerated
        calib_data = DataStore.calib_store(data_dir)
        del calib_data[changes[0]['idx']:]
        calib_data.flush()
    # done
    return 0

if __name__ == "__main__":
    sys.exit(main())
