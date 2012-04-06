#!/usr/bin/env python

"""
Predict future weather using recent data.

usage: python Forecast.py [options] data_dir
options are:
 -h | --help  display this help
data_dir is the root directory of the weather data
"""

from datetime import datetime, timedelta
import getopt
import sys

import DataStore
import Localisation
from TimeZone import Local, utc
import ZambrettiCore

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
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    for o, a in opts:
        if o in ('-h', '--help'):
            print __doc__.strip()
            return 0
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, "Error: 1 argument required"
        print >>sys.stderr, __doc__.strip()
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
