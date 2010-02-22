#!/usr/bin/env python

"""
Save weather station history to file.

usage: python LogData.py [options] data_dir
options are:
\t--help\t\t\tdisplay this help
data_dir is the root directory of the weather data
"""

from datetime import datetime, timedelta
import getopt
import os
import sys
import time

import DataStore
from TimeZone import Local
import WeatherStation

def LogData(params, raw_data, verbose=1):
    # connect to weather station
    ws = WeatherStation.weather_station()
    fixed_block = ws.get_fixed_block()
    if not fixed_block:
        print >>sys.stderr, "Invalid data from weather station"
        return 3
    # synchronise with weather station's logging time
    if verbose > 0:
        print 'Synchronising with weather station'
    current_ptr = ws.current_pos()
    data = ws.get_data(current_ptr, unbuffered=True)
    last_delay = data['delay']
    while data['delay'] == last_delay:
        last_delay = data['delay']
        time.sleep(5)
        current_ptr = ws.current_pos()
        data = ws.get_data(current_ptr, unbuffered=True)
    last_date = datetime.utcnow().replace(microsecond=0) - \
                timedelta(minutes=data['delay'])
    last_ptr = ws.dec_ptr(current_ptr)
    # re-read fixed block, just in case we read it at an unstable time
    fixed_block = ws.get_fixed_block(unbuffered=True)
    # check clocks
    s_time = DataStore.safestrptime(
        fixed_block['date_time'], '%Y-%m-%d %H:%M') + timedelta(seconds=30)
    c_time = datetime.now()
    diff = abs(s_time - c_time)
    if diff > timedelta(minutes=2):
        print >>sys.stderr, \
              """WARNING: computer and weather station clocks disagree by %s (H:M:S).
Check that the computer is synchronised to a network time server and
that the weather station clock is correct. If the station has a radio
controlled clock, it may have lost its signal.""" % (str(diff))
    # store info from fixed block
    pressure_offset = fixed_block['rel_pressure'] - fixed_block['abs_pressure']
    params.set('fixed', 'pressure offset', '%g' % (pressure_offset))
    params.set('fixed', 'read period', '%d' % (fixed_block['read_period']))
    # get time to go back to
    last_stored = raw_data.before(datetime.max)
    if last_stored == None:
        last_stored = datetime.min
    else:
        last_stored = last_stored + \
                      timedelta(minutes=fixed_block['read_period'] / 2)
    # go back through stored data, until we catch up with what we've already got
    if verbose > 0:
        print 'Fetching data'
    count = 0
    while last_ptr != current_ptr and last_date > last_stored:
        count += 1
        if count >= fixed_block['data_count']:
            break
        data = ws.get_data(last_ptr)
        if data['delay'] == None:
            break
        raw_data[last_date] = data
        last_date = last_date - timedelta(minutes=data['delay'])
        last_ptr = ws.dec_ptr(last_ptr)
    if verbose > 0:
        print "%d records written" % count
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
    root_dir = args[0]
    return LogData(DataStore.params(root_dir),
                   DataStore.data_store(root_dir))
if __name__ == "__main__":
    sys.exit(main())
