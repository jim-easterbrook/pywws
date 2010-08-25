#!/usr/bin/env python
"""
Post weather update to WeatherUnderground.

usage: python ToUnderground.py [options] data_dir
options are:
  -h or --help     display this help
  -c or --catchup  upload all data since last upload (up to 4 weeks)
  -v or --verbose  increase amount of reassuring messages
data_dir is the root directory of the weather data

StationID and password are read from the weather.ini file in data_dir.
"""

import getopt
import sys
import urllib
import urllib2
from datetime import datetime, timedelta

import DataStore
from TimeZone import Local, utc
from WeatherStation import dew_point

def CtoF(C):
    return (C * 9.0 / 5.0) + 32.0
class ToUnderground:
    def __init__(self, params, raw_data, verbose=1, rapid_fire=False):
        self.params = params
        self.data = raw_data
        self.verbose = verbose
        self.rapid_fire = rapid_fire
        self.pressure_offset = eval(params.get('fixed', 'pressure offset'))
        if self.rapid_fire:
            self.server = 'rtupdate.wunderground.com'
        else:
            self.server = 'weatherstation.wunderground.com'
        self.url = 'http://%s/weatherstation/updateweatherstation.php' % self.server
        self.rain_midnight = None
        # compute local midnight
        self.midnight = datetime.utcnow().replace(tzinfo=utc).astimezone(
            Local).replace(hour=0, minute=0, second=0).astimezone(
                utc).replace(tzinfo=None)
        self.day = timedelta(hours=24)
        self.hour = timedelta(hours=1)
        # set fixed part of upload data
        password = self.params.get('underground', 'password', 'undergroudpassword')
        station = self.params.get('underground', 'station', 'undergroundstation')
        self.fixed_data = {}
        self.fixed_data['action'] = 'updateraw'
        self.fixed_data['softwaretype'] = 'pywws'
        self.fixed_data['ID'] = station
        self.fixed_data['PASSWORD'] = password
        if self.rapid_fire:
            self.fixed_data['realtime'] = '1'
            self.fixed_data['rtfreq'] = '48'
    def TranslateData(self, current):
        # get rain data for 1 hr ago and local midnight
        rain_hour = self.data[self.data.nearest(current['idx'] - self.hour)]['rain']
        while current['idx'] < self.midnight:
            self.midnight -= self.day
            self.rain_midnight = None
        while current['idx'] >= self.midnight + self.day:
            self.midnight += self.day
            self.rain_midnight = None
        if self.rain_midnight == None:
            self.rain_midnight = self.data[self.data.nearest(self.midnight)]['rain']
        # create weather underground command
        result = dict(self.fixed_data)
        result['dateutc'] = current['idx'].isoformat(' ')
        if current['wind_dir'] != None and current['wind_dir'] < 16:
            result['winddir'] = '%.0f' % (current['wind_dir'] * 22.5)
        if current['temp_out'] != None:
            result['tempf'] = '%.1f' % (CtoF(current['temp_out']))
            if current['hum_out'] != None:
                result['dewptf'] = '%.1f' % (
                    CtoF(dew_point(current['temp_out'], current['hum_out'])))
                result['humidity'] = '%d' % (current['hum_out'])
        if current['wind_ave'] != None:
            result['windspeedmph'] = '%.2f' % (current['wind_ave'] * 3.6 / 1.609344)
        if current['wind_gust'] != None:
            result['windgustmph'] = '%.2f' % (current['wind_gust'] * 3.6 / 1.609344)
        result['rainin'] = '%g' % (max(current['rain'] - rain_hour, 0.0) / 25.4)
        result['dailyrainin'] = '%g' % (
            max(current['rain'] - self.rain_midnight, 0.0) / 25.4)
        result['baromin'] = '%.2f' % (
            (current['abs_pressure'] + self.pressure_offset) * 0.02953)
        return result
    def SendData(self, data):
        # upload data
        if self.verbose > 2:
            print data
        # create weather underground command
        getPars = self.TranslateData(data)
        if self.verbose > 1:
            print getPars
        # convert command to URL
        full_url = self.url + '?' + urllib.urlencode(getPars)
        if self.verbose > 2:
            print full_url
        wudata = urllib2.urlopen(full_url)
        moreinfo = wudata.read()
        if self.verbose > 0:
            print "Weather Underground returns: \"%s\"" % (moreinfo.strip())
    def Upload(self, catchup):
        if catchup:
            # upload all data since last time
            last_update = self.params.get('underground', 'last update')
            if last_update:
                last_update = DataStore.safestrptime(last_update) + timedelta(minutes=1)
            else:
                last_update = datetime.utcnow() - timedelta(days=14)
            # iterate over all data since last_update
            for data_now in self.data[last_update:]:
                self.SendData(data_now)
                last_update = data_now['idx']
        else:
            # upload most recent data
            last_update = self.data.before(datetime.max)
            self.SendData(self.data[last_update])
        self.params.set('underground', 'last update', last_update.isoformat(' '))
        return 0
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hcv", ['help', 'catchup', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    catchup = False
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
        elif o == '-c' or o == '--catchup':
            catchup = True
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, "Error: 1 argument required"
        print >>sys.stderr, __doc__.strip()
        return 2
    return ToUnderground(
        DataStore.params(args[0]), DataStore.data_store(args[0]),
        verbose=verbose).Upload(catchup)
if __name__ == "__main__":
    sys.exit(main())
