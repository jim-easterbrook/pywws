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
import logging
import sys
import urllib
import urllib2
from datetime import datetime, timedelta

import DataStore
from Logger import ApplicationLogger
from TimeZone import Local, utc
from WeatherStation import dew_point

def CtoF(C):
    return (C * 9.0 / 5.0) + 32.0
class ToUnderground(object):
    def __init__(self, params, raw_data):
        self.logger = logging.getLogger('pywws.ToUnderground')
        self.params = params
        self.data = raw_data
        self.old_result = None
        self.old_ex = None
        self.pressure_offset = eval(params.get('fixed', 'pressure offset'))
        # Weather Underground server, normal and rapid fire
        self.server = (
            'weatherstation.wunderground.com', 'rtupdate.wunderground.com')
        self.rain_midnight = None
        # compute local midnight
        self.midnight = datetime.utcnow().replace(tzinfo=utc).astimezone(
            Local).replace(hour=0, minute=0, second=0).astimezone(
                utc).replace(tzinfo=None)
        self.day = timedelta(hours=24)
        self.hour = timedelta(hours=1)
        self.five_mins = timedelta(minutes=5)
        # set fixed part of upload data, versions for normal and rapid fire
        password = self.params.get('underground', 'password', 'undergroudpassword')
        station = self.params.get('underground', 'station', 'undergroundstation')
        self.fixed_data = ({}, {})
        for i in False, True:
            self.fixed_data[i]['action'] = 'updateraw'
            self.fixed_data[i]['softwaretype'] = 'pywws'
            self.fixed_data[i]['ID'] = station
            self.fixed_data[i]['PASSWORD'] = password
        self.fixed_data[True]['realtime'] = '1'
        self.fixed_data[True]['rtfreq'] = '48'
    def _TranslateData(self, current, rapid_fire):
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
        result = dict(self.fixed_data[rapid_fire])
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
    def SendData(self, data, rapid_fire):
        # create weather underground command
        getPars = self._TranslateData(data, rapid_fire)
        # convert command to URL
        url = 'http://%s/weatherstation/updateweatherstation.php?%s' % (
            self.server[rapid_fire], urllib.urlencode(getPars))
        self.logger.debug(url)
        # have three tries before giving up
        for n in range(3):
            try:
                wudata = urllib2.urlopen(url)
                moreinfo = wudata.read()
                result = moreinfo.strip()
                if result == 'success':
                    self.logger.debug(
                        "Weather Underground returns: %s", result)
                    break
                elif result != self.old_result:
                    self.logger.error(
                        "Weather Underground returns: %s", result)
                    self.old_result = result
            except Exception, ex:
                e = str(ex)
                if e != self.old_ex:
                    self.logger.error(e)
                    self.old_ex = e
    def Upload(self, catchup):
        if catchup:
            # upload all data since last time
            last_update = self.params.get('underground', 'last update')
            if last_update:
                start = DataStore.safestrptime(last_update) + timedelta(minutes=1)
            else:
                start = datetime.utcnow() - timedelta(days=7)
            # iterate over all data since last_update
            count = 0
            for data in self.data[start:]:
                self.SendData(data, False)
                count += 1
            if count:
                self.logger.info('%d records sent', count)
            last_update = self.data.before(datetime.max)
        else:
            # upload most recent data
            last_update = self.data.before(datetime.max)
            self.SendData(self.data[last_update], False)
        self.params.set('underground', 'last update', last_update.isoformat(' '))
        return 0
    def RapidFire(self, data, catchup):
        last_log = self.data.before(datetime.max)
        if last_log < data['idx'] - self.five_mins:
            # logged data is not (yet) up to date
            return
        if catchup:
            last_update = self.params.get('underground', 'last update')
            if last_update:
                last_update = DataStore.safestrptime(last_update)
            else:
                last_update = datetime.min
            if last_update <= last_log - self.five_mins:
                # last update was well before last logged data
                self.Upload(True)
        self.SendData(data, True)
        self.params.set('underground', 'last update', data['idx'].isoformat(' '))
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
    logger = ApplicationLogger(verbose)
    return ToUnderground(
        DataStore.params(args[0]), DataStore.data_store(args[0])).Upload(catchup)
if __name__ == "__main__":
    sys.exit(main())
