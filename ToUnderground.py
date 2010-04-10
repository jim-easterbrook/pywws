#!/usr/bin/env python
"""
Post weather update to WeatherUnderground.

usage: python ToUnderground.py [options] data_dir
options are:
\t--help\t\tdisplay this help
\t-v or --verbose\tincrease amount of reassuring messages
data_dir is the root directory of the weather data

StationID and password are read from the weather.ini file in data_dir.
"""

import getopt
import sys
import urllib
import urllib2
from datetime import datetime, timedelta

import DataStore
from WeatherStation import dew_point

def ToUnderground(params, data, verbose=1):
    password = params.get('underground', 'password', 'undergroudpassword')
    station = params.get('underground', 'station', 'undergroundstation')
    # most recent data can't be to this very second so will always be before now
    data_now = data[data.before(datetime.max)]
    data_prev = data[data.nearest(data_now['idx'] - timedelta(hours=1))]
    if verbose > 1:
        print data_now
    # create weather underground command
    getPars = {}
    getPars['action'] = 'updateraw'
    getPars['ID'] = station
    getPars['PASSWORD'] = password
    getPars['dateutc'] = data_now['idx'].isoformat(' ')
    getPars['winddir'] = '%.0f' % (data_now['wind_dir'] * 22.5)
    getPars['tempf'] = '%.1f' % ((data_now['temp_out'] * 9.0 / 5.0) + 32.0)
    getPars['dewptf'] = '%.1f' % (
        (dew_point(data_now['temp_out'], data_now['hum_out']) * 9.0 / 5.0) + 32.0)
    getPars['windspeedmph'] = '%.2f' % (data_now['wind_ave'] / 1.609344)
    getPars['windgustmph'] = '%.2f' % (data_now['wind_gust'] / 1.609344)
    getPars['humidity'] = '%d' % (data_now['hum_out'])
    getPars['rainin'] = '%g' % (max(data_now['rain'] - data_prev['rain'], 0.0) / 25.4)
    getPars['baromin'] = '%.2f' % (data_now['abs_pressure'] * 0.02953)
    if verbose > 1:
        print getPars
    # convert command to URL
    url = 'http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
    full_url = url + '?' + urllib.urlencode(getPars)
    if verbose > 2:
        print full_url
    wudata = urllib2.urlopen(full_url)
    moreinfo = wudata.read()
    if verbose > 0:
        print "Weather Underground returns: \"%s\"" % (moreinfo.strip())
    return 0
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, "Error: 1 argument required"
        print >>sys.stderr, __doc__.strip()
        return 2
    return ToUnderground(
        DataStore.params(args[0]), DataStore.data_store(args[0]), verbose)
if __name__ == "__main__":
    sys.exit(main())
