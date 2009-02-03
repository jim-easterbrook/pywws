#!/usr/bin/env python
"""
Convert EasyWeather.dat data to pywws format.

usage: python EWtoPy.py [options] EasyWeather_file data_dir
options are:
\t-h or --help\t\tdisplay this help
EasyWeather_file is the input data file, e.g. EasyWeather.dat
data_dir is the root directory of the weather data
"""

import datetime
import getopt
import os
import sys

import DataStore

def main(argv=None):
    dst = True  # known state at start of my Easyweather.dat file
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # check arguments
    if len(args) != 2:
        print >>sys.stderr, 'Error: 2 arguments required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    # process options
    for o, a in opts:
        if o == '--help':
            usage()
            return 0
    # process arguments
    in_name = args[0]
    out_name = args[1]
    # open input
    in_file = open(in_name, 'r')
    # open data file store
    ds = DataStore.data_store(out_name)
    # get time to go forward to
    first_stored = ds.after(datetime.datetime.min)
    if first_stored == None:
        first_stored = datetime.datetime.max
    # copy any missing data
    last_date = None
    count = 0
    for line in in_file:
        items = line.split(',')
        date = datetime.datetime.strptime(items[2].strip(), '%Y-%m-%d %H:%M:%S')
        # get data
        data = {}
        data['delay'] = int(items[3])
        data['hum_in'] = int(items[4])
        data['temp_in'] = float(items[5])
        try:
            data['hum_out'] = int(items[6])
        except:
            data['hum_out'] = None
        try:
            data['temp_out'] = float(items[7])
        except:
            data['temp_out'] = None
        data['pressure'] = float(items[10])
        try:
            data['wind_ave'] = float(items[12])
        except:
            data['wind_ave'] = None
        try:
            data['wind_gust'] = float(items[14])
        except:
            data['wind_gust'] = None
        try:
            data['wind_dir'] = int(items[16])
        except:
            data['wind_dir'] = None
        data['rain'] = int(items[18]) * 0.3
        data['status'] = int(items[35].split()[15], 16)
        # detect change in DST
        if last_date:
            diff = (date - last_date) - datetime.timedelta(minutes=data['delay'])
            if dst and diff < datetime.timedelta(minutes=-55):
                print "DST -> off", date
                dst = False
            if not dst and diff > datetime.timedelta(minutes=55):
                print "DST -> on", date
                dst = True
        last_date = date
        # adjust date for DST
        if dst:
            date = date - datetime.timedelta(hours=1)
        # check against first_stored
        if first_stored - date < datetime.timedelta(minutes=data['delay'] / 2):
            break
        ds[date] = data
        count += 1
    print "%d records written" % count
    in_file.close()
    del ds
    return 0
if __name__ == "__main__":
    sys.exit(main())
