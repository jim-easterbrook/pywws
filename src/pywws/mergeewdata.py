# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-21  pywws contributors

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

"""Convert EasyWeather.dat data to pywws format
::

%s

Introduction
------------

This module converts data from the format used by the EasyWeather
program supplied with the weather station to the format used by pywws.
It is useful if you've been using EasyWeather for a while before
discovering pywws.

The ``EasyWeather.dat`` file is only used to provide data from before
the start of the pywws data. As your weather station has its own memory,
you should run :py:mod:`pywws.logdata` before
:py:mod:`pywws.mergeewdata` to minimise use of the EasyWeather.dat file.

:py:mod:`pywws.mergeewdata` converts the time stamps in EasyWeather.dat
from local time to UTC. This can cause problems when daylight savings
time ends, as local time appears to jump back one hour. The program
attempts to detect this and correct the affected time stamps, but I have
not been able to test this on a variety of time zones.

Detailed API
------------

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.mergeewdata [options] EasyWeather_file data_dir
 options are:
  -h or --help    display this help
 EasyWeather_file is the input data file, e.g. EasyWeather.dat
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

from datetime import datetime, timedelta
import getopt
import os
import sys

import pywws.storage
from pywws.timezone import time_zone


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 1
    # process options
    for o, a in opts:
        if o in ('-h', '--help'):
            print(__usage__.strip(), file=sys.stderr)
            return 0
    # check arguments
    if len(args) != 2:
        print('Error: 2 arguments required\n', file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 2
    # process arguments
    in_name = args[0]
    out_name = args[1]
    # open input
    in_file = open(in_name, 'r')
    # open data store via PywwsContext
    ds = pywws.storage.PywwsContext(out_name,False).raw_data
    # get time to go forward to
    first_stored = ds.after(datetime.min)
    if first_stored == None:
        first_stored = datetime.max
    # copy any missing data
    last_date = None
    count = 0
    for line in in_file:
        items = line.split(',')
        local_date = datetime.strptime(items[2].strip(), '%Y-%m-%d %H:%M:%S')
        date = time_zone.local_to_utc(local_date)
        if last_date and date < last_date:
            date = date + timedelta(hours=1)
            print("Corrected DST ambiguity %s -> %s" % (local_date, date))
        last_date = date
        # get data
        data = {}
        data['delay'] = int(items[3])
        data['hum_in'] = int(items[4])
        data['temp_in'] = float(items[5])
        try:
            data['hum_out'] = int(items[6])
        except Exception:
            data['hum_out'] = None
        try:
            data['temp_out'] = float(items[7])
        except Exception:
            data['temp_out'] = None
        data['abs_pressure'] = float(items[10])
        try:
            data['wind_ave'] = float(items[12])
        except Exception:
            data['wind_ave'] = None
        try:
            data['wind_gust'] = float(items[14])
        except Exception:
            data['wind_gust'] = None
        try:
            data['wind_dir'] = int(items[16])
        except Exception:
            data['wind_dir'] = None
        data['rain'] = int(items[18]) * 0.3
        data['status'] = int(items[35].split()[15], 16)
        # check against first_stored
        if first_stored - date < timedelta(minutes=data['delay'] // 2):
            break
        ds[date] = data
        count += 1
    print("%d records written" % count)
    in_file.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
