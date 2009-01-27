#!/usr/bin/env python

from datetime import datetime, timedelta
import getopt
import os
import sys
import time

import DataStore
import WeatherStation

def LogData(params, raw_data):
    # connect to weather station
    ws = WeatherStation.weather_station()
    fixed_block = ws.get_fixed_block()
    if not fixed_block:
        print >>sys.stderr, "Invalid data from weather station"
        return 3
    # store info from fixed block
    params.set('fixed', 'pressure offset', '%g' % (
        fixed_block['rel_pressure'] - fixed_block['abs_pressure']))
    params.set('fixed', 'read period', '%d' % (fixed_block['read_period']))
    # get time to go back to
    last_stored = raw_data.before(datetime.max)
    if last_stored == None:
        last_stored = datetime.min
    else:
        last_stored = last_stored + \
                      timedelta(minutes=fixed_block['read_period'] / 2)
    # synchronise with weather station's logging time
    print 'Synchronising with weather station'
    next_delay = -2
    while True:
        current_ptr = ws.current_pos()
        data = ws.get_data(current_ptr, unbuffered=True)
        if data['delay'] == next_delay:
            # just had an increase in delay
            break
        next_delay = (data['delay'] + 1) % fixed_block['read_period']
        time.sleep(5)
    last_date = datetime.utcnow().replace(microsecond=0) - \
                timedelta(minutes=next_delay)
    last_ptr = ws.dec_ptr(current_ptr)
    # go back through stored data, until we catch up with what we've already got
    print 'Fetching data'
    count = 0
    while last_ptr != current_ptr and last_date > last_stored:
        data = ws.get_data(last_ptr)
        raw_data[last_date] = data
        count += 1
        last_date = last_date - timedelta(minutes=data['delay'])
        last_ptr = ws.dec_ptr(last_ptr)
    print "%d records written" % count
def usage():
    print >>sys.stderr, 'usage: %s [options] data_directory' % sys.argv[0]
    print >>sys.stderr, '''\toptions are:
    \t--help\t\t\tdisplay this help'''
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, msg
        usage()
        return 1
    # process options
    for o, a in opts:
        if o == '--help':
            usage()
            return 0
    # process arguments
    if len(args) != 1:
        print >>sys.stderr, "must specify data directory"
        usage()
        return 2
    root_dir = args[0]
    return LogData(DataStore.params(root_dir),
                   DataStore.data_store(root_dir))
if __name__ == "__main__":
    sys.exit(main())
