#!/usr/bin/env python

"""
Test connection to weather station.

usage: python TestWeatherStation.py [options]
options are:
\t-d | --decode\t\tdisplay meaningful values instead of raw data
\t-h | --history count\tdisplay the last "count" readings
\t--help\t\t\tdisplay this help
"""

import datetime
import getopt
import WeatherStation
import sys

def raw_dump(pos, data):
    print "%04x" % pos,
    for item in data:
        print "%02x" % item,
    print
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "dh:", ['decode', 'history=', 'help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # check arguments
    if len(args) != 0:
        print >>sys.stderr, 'Error: no arguments allowed\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    # process options
    history_count = 0
    decode = False
    for o, a in opts:
        if o == '-d' or o == '--decode':
            decode = True
        if o == '-h' or o == '--history':
            history_count = int(a)
        if o == '--help':
            print __doc__.strip()
            return 0
    # do it!
    ws = WeatherStation.weather_station()
    raw_fixed = ws.get_raw_fixed_block()
    if not raw_fixed:
        print "No valid data block found"
        return 3
    if decode:
        decoded_fixed = ws.get_fixed_block()
        # dump entire fixed block
        print decoded_fixed
        # dump a few selected items
        print "min -> temp_out ->", ws.get_fixed_block(['min', 'temp_out'])
        print "alarm -> hum_out ->", ws.get_fixed_block(['alarm', 'hum_out'])
        print "rel_pressure ->", ws.get_fixed_block(['rel_pressure'])
        print "abs_pressure ->", ws.get_fixed_block(['abs_pressure'])
    else:
        for ptr in range(0x0000, 0x0100, 0x20):
            raw_dump(ptr, raw_fixed[ptr:ptr+0x20])
    if history_count > 0:
        lo_fix = ws.get_lo_fix_block()
        print "Recent history", lo_fix
        ptr = lo_fix['current_pos']
        date = datetime.datetime.strptime(lo_fix['date_time'], '%Y-%m-%d %H:%M')
        for i in range(history_count):
            if decode:
                data = ws.get_data(ptr)
                print date, data
                date = date - datetime.timedelta(minutes=data['delay'])
            else:
                raw_dump(ptr, ws.get_raw_data(ptr))
            ptr = ws.dec_ptr(ptr)
    del ws
    return 0
if __name__ == "__main__":
    sys.exit(main())