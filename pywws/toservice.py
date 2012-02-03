#!/usr/bin/env python

"""Base class for Weather Underground and UK Met Office uploaders.

"""

import getopt
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

FIVE_MINS = timedelta(minutes=5)
HOUR = timedelta(hours=1)
DAY = timedelta(hours=24)

default_params = {
    'metoffice' : {
        'url'       : 'http://wow.metoffice.gov.uk/automaticreading',
        'header'    : {
            'siteid'                : '12345678',
            'siteAuthenticationKey' : '987654',
            },
        'data'      : (
            'tempf', 'dewptf', 'humidity', 'baromin',
            'windspeedmph', 'windgustmph', 'winddir',
            'rainin', 'dailyrainin',
            ),
        },
    'stacjapogodywawpl' : {
        'url'       : 'http://stacjapogody.waw.pl/mapastacji/uploadweatherstationdata.php',
        'header'    : {
            'action'    : 'updateraw',
            'ID'        : 'stacjapogodywawplstation',
            'PASSWORD'  : 'stacjapogodywawplpassword',
            },
        'data'      : (
            'tempf', 'dewptf', 'humidity', 'baromin',
            'windspeedmph', 'windgustmph', 'winddir',
            'rainin', 'dailyrainin',
            'UV', 'solarradiation',
            ),
        },
    'stacjapogodywawpl-rf' : {
        'url'   : 'http://stacjapogody.waw.pl/mapastacji/uploadweatherstationdata.php',
        },
    'underground' : {
        'url'       : 'http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php',
        'header'    : {
            'action'    : 'updateraw',
            'ID'        : 'undergroundstation',
            'PASSWORD'  : 'undergroudpassword',
            },
        'data'      : (
            'tempf', 'dewptf', 'humidity', 'baromin',
            'windspeedmph', 'windgustmph', 'winddir',
            'rainin', 'dailyrainin',
            'UV', 'solarradiation',
            ),
        },
    'underground-rf' : {
        'url'   : 'http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php',
        },
    }

class ToService(object):
    """Base class for 'Weather Underground' style weather service
    uploaders.

    Derived classes must call the base class constructor. They will
    also want to call the :meth:`upload` method, but may also call
    other methods.

    """
    def __init__(self, params, calib_data, service_name=None):
        """

        :param params: pywws configuration.

        :type params: :class:`pywws.DataStore.params`
        
        :param calib_data: 'calibrated' data.

        :type calib_data: :class:`pywws.DataStore.calib_store`
    
        """
        if service_name:
            self.config_section = service_name
            self.logger = logging.getLogger(
                'pywws.ToService(%s)' % service_name)
        else:
            self.logger = logging.getLogger(
                'pywws.%s' % self.__class__.__name__)
        self.params = params
        self.data = calib_data
        self.old_response = None
        self.old_ex = None
        # set default socket timeout, so urlopen calls don't hang forever
        socket.setdefaulttimeout(10)
        # compute local midnight
        self.midnight = datetime.utcnow().replace(tzinfo=utc).astimezone(
            Local).replace(hour=0, minute=0, second=0).astimezone(
                utc).replace(tzinfo=None)
        # other init
        self.rain_midnight = None
        # get URL
        if self.config_section in default_params:
            default = default_params[self.config_section]['url']
        else:
            default = 'http://example.com/upload'
        self.server = self.params.get(self.config_section, 'url', default)
        # get fixed part of upload data
        if self.config_section in default_params:
            default = default_params[self.config_section]['header']
        else:
            default = {
                'action'    : 'updateraw',
                'ID'        : 'ABC123',
                'PASSWORD'  : 'secret',
                }
        self.fixed_data = eval(
            self.params.get(self.config_section, 'header', str(default)))
        self.fixed_data['softwaretype'] = 'pywws'
        # get other parameters
        self.catchup = eval(
            self.params.get(self.config_section, 'catchup', '7'))
        self.rapid_fire = eval(
            self.params.get(self.config_section, 'rapidfire', 'False'))
        if self.rapid_fire:
            rf_name = '%s-rf' % self.config_section
            # get rapid fire URL
            if rf_name in default_params:
                default = default_params[rf_name]['url']
            else:
                default = 'http://rt.example.com/upload'
            self.server_rf = self.params.get(rf_name, 'url', default)
            # set rapid fire header
            self.fixed_data_rf = dict(self.fixed_data)
            self.fixed_data_rf['realtime'] = '1'
            self.fixed_data_rf['rtfreq'] = '48'
        # list of data to be sent
        if self.config_section in default_params:
            default = default_params[self.config_section]['data']
        else:
            default = (
                'tempf', 'dewptf', 'humidity', 'baromin',
                'windspeedmph', 'windgustmph', 'winddir',
                'rainin', 'dailyrainin',
                'UV', 'solarradiation',
                )
        self.data_items = eval(
            self.params.get(self.config_section, 'data', str(default)))

    def translate_data(self, current, fixed_data):
        """Convert a weather data record to upload format.

        The :obj:`current` parameter contains the data to be uploaded.
        It should be a 'calibrated' data record, as stored in
        :class:`pywws.DataStore.calib_store`.

        The :obj:`fixed_data` parameter contains unvarying data that
        is site dependent, for example an ID code and authentication
        data.

        :param current: the weather data record.

        :type current: dict

        :param fixed_data: unvarying upload data.

        :type fixed_data: dict

        :return: converted data, or :obj:`None` if invalid data.

        :rtype: dict(string)
        
        """
        # check we have enough data
        if current['temp_out'] is None or current['hum_out'] is None:
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
        # convert data
        result = dict(fixed_data)
        result['dateutc'] = current['idx'].isoformat(' ')
        if 'winddir' in self.data_items and current['wind_dir'] is not None:
            result['winddir'] = '%.0f' % (current['wind_dir'] * 22.5)
        if 'tempf' in self.data_items:
            result['tempf'] = '%.1f' % (conversions.temp_f(current['temp_out']))
        if 'dewptf' in self.data_items:
            result['dewptf'] = '%.1f' % (conversions.temp_f(
                    dew_point(current['temp_out'], current['hum_out'])))
        if 'humidity' in self.data_items:
            result['humidity'] = '%d' % (current['hum_out'])
        if 'windspeedmph' in self.data_items and current['wind_ave'] is not None:
            result['windspeedmph'] = '%.2f' % (
                conversions.wind_mph(current['wind_ave']))
        if 'windgustmph' in self.data_items and current['wind_gust'] is not None:
            result['windgustmph'] = '%.2f' % (
                conversions.wind_mph(current['wind_gust']))
        if 'rainin' in self.data_items:
            result['rainin'] = '%g' % (
                conversions.rain_inch(max(current['rain'] - rain_hour, 0.0)))
        if 'dailyrainin' in self.data_items:
            result['dailyrainin'] = '%g' % (
                conversions.rain_inch(max(current['rain'] - self.rain_midnight, 0.0)))
        if 'baromin' in self.data_items and current['rel_pressure']:
            result['baromin'] = '%.4f' % (
                conversions.pressure_inhg(current['rel_pressure']))
        if current.has_key('uv'):
            if 'UV' in self.data_items and current['uv'] is not None:
                result['UV'] = '%d' % (current['uv'])
            if ('illuminance' in self.data_items and
                    current['illuminance'] is not None):
                # approximate conversion from lux to W/m2
                result['solarradiation'] = '%.2f' % (
                    current['illuminance'] * 0.005)
        return result

    def send_data(self, data, server, fixed_data):
        """Upload a weather data record.

        The :obj:`data` parameter contains the data to be uploaded.
        It should be a 'calibrated' data record, as stored in
        :class:`pywws.DataStore.calib_store`.

        The :obj:`fixed_data` parameter contains unvarying data that
        is site dependent, for example an ID code and authentication
        data.

        :param data: the weather data record.

        :type data: dict

        :param server: web address to upload to.

        :type server: string

        :param fixed_data: unvarying upload data.

        :type fixed_data: dict

        :return: success status

        :rtype: bool
        
        """
        coded_data = self.translate_data(data, fixed_data)
        if not coded_data:
            return True
        coded_data = urllib.urlencode(coded_data)
        self.logger.debug(coded_data)
        # have three tries before giving up
        for n in range(3):
            try:
                wudata = urllib.urlopen(server, coded_data)
                response = wudata.readlines()
                wudata.close()
                if response != self.old_response:
                    for line in response:
                        self.logger.error(line.strip())
                    self.old_response = response
                if not response:
                    # Met office returns empty array on success
                    return True
                if response[0] == 'success\n':
                    # Weather Underground returns 'success' string
                    return True
            except Exception, ex:
                e = str(ex)
                if e != self.old_ex:
                    self.logger.error(e)
                    self.old_ex = e
        return False

    def Upload(self, catchup):
        """Upload one or more weather data records.

        This method uploads either the most recent weather data
        record, or all records since the last upload (up to 7 days),
        according to the value of :obj:`catchup`.

        It sets the ``last update`` configuration value to the time
        stamp of the most recent record successfully uploaded.

        :param catchup: upload all data since last upload.

        :type catchup: bool

        :return: success status

        :rtype: bool
        
        """
        if catchup and self.catchup > 0:
            start = datetime.utcnow() - timedelta(days=self.catchup)
            last_update = self.params.get_datetime(
                self.config_section, 'last update')
            if last_update:
                start = max(start, last_update + timedelta(minutes=1))
            count = 0
            for data in self.data[start:]:
                if not self.send_data(data, self.server, self.fixed_data):
                    return False
                self.params.set(
                    self.config_section, 'last update', data['idx'].isoformat(' '))
                count += 1
            if count:
                self.logger.info('%d records sent', count)
        else:
            # upload most recent data
            last_update = self.data.before(datetime.max)
            if not self.send_data(
                    self.data[last_update], self.server, self.fixed_data):
                return False
            self.params.set(
                self.config_section, 'last update', last_update.isoformat(' '))
        return True

    def RapidFire(self, data, catchup):
        """Upload a 'Rapid Fire' weather data record.

        This method uploads either a single data record (typically one
        obtained during 'live' logging), or all records since the last
        upload (up to 7 days), according to the value of
        :obj:`catchup`.

        It sets the ``last update`` configuration value to the time
        stamp of the most recent record successfully uploaded.

        The :obj:`data` parameter contains the data to be uploaded.
        It should be a 'calibrated' data record, as stored in
        :class:`pywws.DataStore.calib_store`.

        :param data: the weather data record.

        :type data: dict

        :param catchup: upload all data since last upload.

        :type catchup: bool

        :return: success status

        :rtype: bool
        
        """
        last_log = self.data.before(datetime.max)
        if not last_log or last_log < data['idx'] - FIVE_MINS:
            # logged data is not (yet) up to date
            return True
        if catchup and self.catchup > 0:
            last_update = self.params.get_datetime(
                self.config_section, 'last update')
            if not last_update:
                last_update = datetime.min
            if last_update <= last_log - FIVE_MINS:
                # last update was well before last logged data
                if not self.Upload(True):
                    return False
        if not self.send_data(data, self.server_rf, self.fixed_data_rf):
            return False
        self.params.set(
            self.config_section, 'last update', data['idx'].isoformat(' '))
        return True

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(
            argv[1:], "hcv", ['help', 'catchup', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    catchup = False
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __usage__.strip()
            return 0
        elif o == '-c' or o == '--catchup':
            catchup = True
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 2:
        print >>sys.stderr, "Error: 2 arguments required"
        print >>sys.stderr, __usage__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    return ToService(
        DataStore.params(args[0]), DataStore.calib_store(args[0]),
        service_name=args[1]
        ).Upload(catchup)

if __name__ == "__main__":
    sys.exit(main())
