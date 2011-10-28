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
    """Base class for 'Weather Underground' style weather service
    uploaders.

    Derived classes must call the base class constructor. They will
    also want to call the :meth:`upload` method, but may also call
    other methods.

    """
    def __init__(self, params, calib_data):
        """

        :param params: pywws configuration.

        :type params: :class:`pywws.DataStore.params`
        
        :param calib_data: 'calibrated' data.

        :type calib_data: :class:`pywws.DataStore.calib_store`
    
        """
        self.logger = logging.getLogger('pywws.%s' % self.__class__.__name__)
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
                        self.logger.error(line)
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

    def upload(self, server, fixed_data, catchup):
        """Upload one or more weather data records.

        This method uploads either the most recent weather data
        record, or all records since the last upload (up to 7 days),
        according to the value of :obj:`catchup`.

        It sets the ``last update`` configuration value to the time
        stamp of the most recent record successfully uploaded.

        The :obj:`fixed_data` parameter contains unvarying data that
        is site dependent, for example an ID code and authentication
        data.

        :param server: web address to upload to.

        :type server: string

        :param fixed_data: unvarying upload data.

        :type fixed_data: dict

        :param catchup: upload all data since last upload.

        :type catchup: bool

        :return: success status

        :rtype: bool
        
        """
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
                if not self.send_data(data, server, fixed_data):
                    return False
                self.params.set(
                    self.config_section, 'last update', data['idx'].isoformat(' '))
                count += 1
            if count:
                self.logger.info('%d records sent', count)
        else:
            # upload most recent data
            last_update = self.data.before(datetime.max)
            if not self.send_data(self.data[last_update], server, fixed_data):
                return False
            self.params.set(
                self.config_section, 'last update', last_update.isoformat(' '))
        return True
