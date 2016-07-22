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

"""Predict future weather using recent data
::

%s

"""

from __future__ import absolute_import

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.Forecast [options] data_dir
 options are:
  -h | --help  display this help
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

from datetime import datetime, timedelta
import getopt
import sys

from pywws import DataStore
from pywws import Localisation
from pywws.TimeZone import Local, utc
from pywws import ZambrettiCore

def ZambrettiCode(params, hourly_data):
    north = eval(params.get('Zambretti', 'north', 'True'))
    baro_upper = eval(params.get('Zambretti', 'baro upper', '1050.0'))
    baro_lower = eval(params.get('Zambretti', 'baro lower', '950.0'))
    if not hourly_data['rel_pressure']:
        return ''
    if hourly_data['wind_ave'] is None or hourly_data['wind_ave'] < 0.3:
        wind = None
    else:
        wind = hourly_data['wind_dir']
    if hourly_data['pressure_trend'] is None:
        trend = 0.0
    else:
        trend = hourly_data['pressure_trend'] / 3.0
    return ZambrettiCore.ZambrettiCode(
        hourly_data['rel_pressure'], hourly_data['idx'].month, wind, trend,
        north=north, baro_top=baro_upper, baro_bottom=baro_lower)

def Zambretti(params, hourly_data):
    code = ZambrettiCode(params, hourly_data)
    return Localisation.translation.ugettext(ZambrettiCore.ZambrettiText(code))

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
            return 0
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, "Error: 1 argument required"
        print >>sys.stderr, __usage__.strip()
        return 2
    data_dir = args[0]
    params = DataStore.params(data_dir)
    Localisation.SetApplicationLanguage(params)
    hourly_data = DataStore.hourly_store(data_dir)
    idx = hourly_data.before(datetime.max)
    print 'Zambretti (current):', Zambretti(params, hourly_data[idx])
    idx = idx.replace(tzinfo=utc).astimezone(Local)
    if idx.hour < 8 or (idx.hour == 8 and idx.minute < 30):
        idx -= timedelta(hours=24)
    idx = idx.replace(hour=9, minute=0, second=0)
    idx = hourly_data.nearest(idx.astimezone(utc).replace(tzinfo=None))
    lcl = idx.replace(tzinfo=utc).astimezone(Local)
    print 'Zambretti (at %s):' % lcl.strftime('%H:%M %Z'), Zambretti(
        params, hourly_data[idx])
    return 0

if __name__ == "__main__":
    sys.exit(main())
