#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-16  pywws contributors

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Set some weather station parameters.

This script can also be run with the ``pywws-setweatherstation`` command. ::
%s

"""

from __future__ import absolute_import

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.SetWeatherStation [options]
 options are:
  -h   | --help           display this help
  -c   | --clock          set weather station clock to computer time
                          (unlikely to work)
  -p f | --pressure f     set relative pressure to f hPa
  -r n | --read_period n  set logging interval to n minutes
  -v   | --verbose        increase error message verbosity
  -z   | --zero_memory    clear the weather station logged reading count
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

from datetime import datetime, timedelta
import getopt
import logging
import sys
import time

from pywws.Logger import ApplicationLogger
from pywws import WeatherStation

def bcd_encode(value):
    hi = value // 10
    lo = value % 10
    return (hi * 16) + lo
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(
            argv[1:], "hcp:r:vz",
            ['help', 'clock', 'pressure=', 'read_period=',
             'verbose', 'zero_memory'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    clock = False
    pressure = None
    read_period = None
    verbose = 0
    zero_memory = False
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
            return 0
        elif o in ('-c', '--clock'):
            clock = True
        elif o in ('-p', '--pressure'):
            pressure = int((float(a) * 10.0) + 0.5)
        elif o in ('-r', '--read_period'):
            read_period = int(a)
        elif o in ('-v', '--verbose'):
            verbose += 1
        elif o in ('-z', '--zero_memory'):
            zero_memory = True
    # check arguments
    if len(args) != 0:
        print >>sys.stderr, "Error: No arguments required"
        print >>sys.stderr, __usage__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    # open connection to weather station
    ws = WeatherStation.weather_station()
    # set data to be sent to station
    data = []
    # set relative pressure
    if pressure:
        ptr = ws.fixed_format['rel_pressure'][0]
        data.append((ptr,   pressure % 256))
        data.append((ptr+1, pressure // 256))
    # set read period
    if read_period:
        data.append((ws.fixed_format['read_period'][0], read_period))
    # reset data count
    if zero_memory:
        ptr = ws.fixed_format['data_count'][0]
        data.append((ptr,   1))
        data.append((ptr+1, 0))
    # set clock
    if clock:
        print "Clock setting is not known to work on any model of weather station."
        print "If it works for you, please let Jim Easterbrook know."
        print "waiting for exact minute"
        now = datetime.now()
        if now.second >= 55:
            time.sleep(10)
            now = datetime.now()
        now += timedelta(minutes=1)
        ptr = ws.fixed_format['date_time'][0]
        data.append((ptr,   bcd_encode(now.year - 2000)))
        data.append((ptr+1, bcd_encode(now.month)))
        data.append((ptr+2, bcd_encode(now.day)))
        data.append((ptr+3, bcd_encode(now.hour)))
        data.append((ptr+4, bcd_encode(now.minute)))
        time.sleep(59 - now.second)
    # send it all in one go
    if data:
        ws.write_data(data)
if __name__ == "__main__":
    sys.exit(main())
