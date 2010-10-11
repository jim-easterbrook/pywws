#!/usr/bin/env python
"""
Set some weather station parameters.

usage: python SetWeatherStation.py [options]
options are:
 -h   | --help           display this help
 -c   | --clock          set weather station clock to computer time
 -r n | --read_period n  set logging interval to n minutes
 -v   | --verbose        increase error message verbosity
"""

from datetime import datetime
import getopt
import logging
import sys
import time

from pywws.Logger import ApplicationLogger
from pywws import WeatherStation

def bcd_encode(value):
    hi = value / 10
    lo = value % 10
    return (hi * 16) + lo
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(
            argv[1:], "hcr:v", ['help', 'clock', 'read_period=', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    clock = False
    read_period = None
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print __doc__.strip()
            return 0
        elif o in ('-c', '--clock'):
            clock = True
        elif o in ('-r', '--read_period'):
            read_period = int(a)
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 0:
        print >>sys.stderr, "Error: No arguments required"
        print >>sys.stderr, __doc__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    # open connection to weather station
    ws = WeatherStation.weather_station()
    # set read period
    if read_period:
        ws.write_data([(ws.fixed_format['read_period'][0], read_period)])
    # set clock
    if clock:
        print "waiting for exact minute"
        now = datetime.now()
        ptr = ws.fixed_format['date_time'][0]
        data = [
            (ptr,   bcd_encode(now.year - 2000)),
            (ptr+1, bcd_encode(now.month)),
            (ptr+2, bcd_encode(now.day)),
            (ptr+3, bcd_encode(now.hour)),
            (ptr+4, bcd_encode(now.minute + 1)),
            ]
        time.sleep(60 - now.second)
        ws.write_data(data)
if __name__ == "__main__":
    sys.exit(main())
