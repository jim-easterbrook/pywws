#!/usr/bin/env python

"""Test quality of USB connection to weather station.

::

%s
"""

__usage__ = """
 usage: python USBQualityTest.py [options]
 options are:
  -h | --help           display this help
  -v | --verbose        increase amount of reassuring messages
                        (repeat for even more messages e.g. -vvv)
"""

__doc__ %= __usage__

__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import sys

from pywws.Logger import ApplicationLogger
from pywws import WeatherStation

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ('help', 'verbose'))
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # check arguments
    if len(args) != 0:
        print >>sys.stderr, 'Error: no arguments allowed\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    # process options
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
            return 0
        elif o in ('-v', '--verbose'):
            verbose += 1
    # do it!
    logger = ApplicationLogger(verbose)
    ws = WeatherStation.weather_station()
    fixed_block = ws.get_fixed_block()
    if not fixed_block:
        print "No valid data block found"
        return 3
    # loop
    ptr = ws.data_start
    total_count = 0
    bad_count = 0
    while True:
        if total_count % 1000 == 0:
            active = ws.current_pos()
        while True:
            ptr += 0x20
            if ptr >= 0x10000:
                ptr = ws.data_start
            if active < ptr - 0x10 or active >= ptr + 0x20:
                break
        result_1 = ws._read_block(ptr, retry=False)
        result_2 = ws._read_block(ptr, retry=False)
        if result_1 != result_2:
            logger.warning('read_block changing %06x', ptr)
            logger.warning('old %s', str(result_1))
            logger.warning('new %s', str(result_2))
            bad_count += 1
        total_count += 1
        print "\r %d/%d " % (bad_count, total_count),
        sys.stdout.flush()
    print ''
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
