"""Base class for Weather Underground and UK Met Office uploaders.

"""

import logging
import socket
import sys
import urllib
from datetime import datetime, timedelta

import conversions
import DataStore
from Logger import ApplicationLogger
from TimeZone import Local, utc
from WeatherStation import dew_point

HOUR = timedelta(hours=1)
DAY = timedelta(hours=24)

class ToService(object):
    def __init__(self, params, calib_data):
        self.logger = logging.getLogger('pywws.%s' % self.__class__.__name__)
        self.params = params
        self.data = calib_data
        self.old_result = None
        self.old_ex = None
        # set default socket timeout, so urlopen calls don't hang forever
        socket.setdefaulttimeout(10)
        # compute local midnight
        self.midnight = datetime.utcnow().replace(tzinfo=utc).astimezone(
            Local).replace(hour=0, minute=0, second=0).astimezone(
                utc).replace(tzinfo=None)
        # other init
        self.rain_midnight = None

    def _translate_data(self, current, fixed_data):
        # check we have enough data
        if (current['temp_out'] is None or
            current['hum_out'] is None):
            return None
        # get rain data for 1 hr ago and local midnight
        rain_hour = self.data[self.data.nearest(current['idx'] - HOUR)]['rain']
        while current['idx'] < self.midnight:
            self.midnight -= DAY
            self.rain_midnight = None
        while current['idx'] >= self.midnight + DAY:
            self.midnight += DAY
            self.rain_midnight = None
        if self.rain_midnight is None:
            self.rain_midnight = self.data[self.data.nearest(self.midnight)]['rain']
        # create weather underground command
        result = dict(fixed_data)
        result['dateutc'] = current['idx'].isoformat(' ')
        if current['wind_dir'] is not None:
            result['winddir'] = '%.0f' % (current['wind_dir'] * 22.5)
        result['tempf'] = '%.1f' % (conversions.temp_f(current['temp_out']))
        result['dewptf'] = '%.1f' % (
            conversions.temp_f(
                dew_point(current['temp_out'], current['hum_out'])))
        result['humidity'] = '%d' % (current['hum_out'])
        if current['wind_ave'] is not None:
            result['windspeedmph'] = '%.2f' % (
                conversions.wind_mph(current['wind_ave']))
        if current['wind_gust'] is not None:
            result['windgustmph'] = '%.2f' % (
                conversions.wind_mph(current['wind_gust']))
        result['rainin'] = '%g' % (
            conversions.rain_inch(max(current['rain'] - rain_hour, 0.0)))
        result['dailyrainin'] = '%g' % (
            conversions.rain_inch(max(current['rain'] - self.rain_midnight, 0.0)))
        if current['rel_pressure']:
            result['baromin'] = '%.4f' % (
                conversions.pressure_inhg(current['rel_pressure']))
        return urllib.urlencode(result)

    def _send_data(self, data, server, fixed_data):
        coded_data = self._translate_data(data, fixed_data)
        if not coded_data:
            return True
        self.logger.debug(coded_data)
        # have three tries before giving up
        for n in range(3):
            try:
                wudata = urllib.urlopen(server, coded_data)
                response = wudata.readlines()
                wudata.close()
                if not response:
                    # Met office returns empty array on success
                    return True
                for line in response:
                    # Weather Underground returns 'success' string
                    if line == 'success\n':
                        return True
                    self.logger.error(line)
            except Exception, ex:
                e = str(ex)
                if e != self.old_ex:
                    self.logger.error(e)
                    self.old_ex = e
        return False

    def _upload(self, server, fixed_data, catchup):
        if catchup:
            last_update = self.params.get_datetime(
                self.config_section, 'last update')
            if last_update:
                # upload all data since last time
                start = last_update + timedelta(minutes=1)
            else:
                # upload one week's data
                start = datetime.utcnow() - timedelta(days=7)
            count = 0
            for data in self.data[start:]:
                if not self._send_data(data, server, fixed_data):
                    return False
                self.params.set(
                    self.config_section, 'last update', data['idx'].isoformat(' '))
                count += 1
            if count:
                self.logger.info('%d records sent', count)
        else:
            # upload most recent data
            last_update = self.data.before(datetime.max)
            if not self._send_data(self.data[last_update], server, fixed_data):
                return False
            self.params.set(
                self.config_section, 'last update', last_update.isoformat(' '))
        return True
