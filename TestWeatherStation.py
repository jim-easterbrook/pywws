#!/usr/bin/env python

"""
Test connection to weather station.

usage: python TestWeatherStation.py [options]
options are:
       --help           display this help
  -3 | --3080           station is a '3080' type instead of a '1080'
  -d | --decode         display meaningful values instead of raw data
  -h | --history count  display the last "count" readings
  -l | --live           display 'live' data
  -u | --unknown        display unknown fixed block values
  -v | --verbose        increase amount of reassuring messages
"""

import datetime
import getopt
import sys

from pywws.DataStore import safestrptime
from pywws.Logger import ApplicationLogger
from pywws import WeatherStation

def raw_dump(pos, data):
    print "%04x" % pos,
    for item in data:
        print "%02x" % item,
    print
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(
            argv[1:], "3dh:luv",
            ('help', '3080', 'decode', 'history=', 'live', 'unknown', 'verbose'))
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
    live = False
    unknown = False
    verbose = 0
    ws_type = '1080'
    for o, a in opts:
        if o == '--help':
            print __doc__.strip()
            return 0
        elif o in ('-3', '--3080'):
            ws_type = '3080'
        elif o in ('-d', '--decode'):
            decode = True
        elif o in ('-h', '--history'):
            history_count = int(a)
        elif o in ('-l', '--live'):
            live = True
        elif o in ('-u', '--unknown'):
            unknown = True
        elif o in ('-v', '--verbose'):
            verbose += 1
    # do it!
    logger = ApplicationLogger(verbose)
    ws = WeatherStation.weather_station(ws_type=ws_type)
    raw_fixed = ws.get_raw_fixed_block()
    if not raw_fixed:
        print "No valid data block found"
        return 3
    if decode:
        # dump entire fixed block
        print ws.get_fixed_block()
        # dump a few selected items
        print "min -> temp_out ->", ws.get_fixed_block(['min', 'temp_out'])
        print "alarm -> hum_out ->", ws.get_fixed_block(['alarm', 'hum_out'])
        print "rel_pressure ->", ws.get_fixed_block(['rel_pressure'])
        print "abs_pressure ->", ws.get_fixed_block(['abs_pressure'])
    else:
        for ptr in range(0x0000, 0x0100, 0x20):
            raw_dump(ptr, raw_fixed[ptr:ptr+0x20])
    if unknown:
        for k in sorted(ws.fixed_format):
            if 'unk' in k:
                print k, ws.get_fixed_block([k])
        for k in sorted(ws.fixed_format):
            if 'settings' in k or 'display' in k or 'alarm' in k:
                bits = ws.get_fixed_block([k])
                for b in sorted(bits):
                    if 'bit' in b:
                        print k, b, bits[b]
    if history_count > 0:
        lo_fix = ws.get_lo_fix_block()
        print "Recent history", lo_fix
        ptr = lo_fix['current_pos']
        date = safestrptime(lo_fix['date_time'], '%Y-%m-%d %H:%M')
        for i in range(history_count):
            if decode:
                data = ws.get_data(ptr)
                print date, data
                date = date - datetime.timedelta(minutes=data['delay'])
            else:
                raw_dump(ptr, ws.get_raw_data(ptr))
            ptr = ws.dec_ptr(ptr)
    if live:
        for data, ptr, logged in ws.live_data():
            print "%04x" % ptr,
            print data['idx'].strftime('%H:%M:%S'),
            del data['idx']
            print data
    del ws
    return 0
if __name__ == "__main__":
    sys.exit(main())