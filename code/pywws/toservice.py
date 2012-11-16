#!/usr/bin/env python

"""Post weather update to services such as Weather Underground
::

%s

Introduction
------------

Several organisations allow weather stations to upload data using a
simple HTTP 'POST' or 'GET' request, with the data encoded as a
sequence of ``key=value`` pairs separated by ``&`` characters.

This module enables pywws to upload readings to these organisations.
It is highly customisable using configuration files. Each 'service'
requires a configuration file and two templates in ``pywws/services``
(that should not need to be edited by the user) and a section in
``weather.ini`` containing user specific data such as your site ID and
password.

There are currently six services for which configuration files have
been written.

+-----------------------------------------------------------------------+-----------------------+------------------------------------------------------------+
| organisation                                                          | service name          | config file                                                |
+=======================================================================+=======================+============================================================+
| `UK Met Office <http://wow.metoffice.gov.uk/>`_                       | ``metoffice``         | :download:`../../code/pywws/services/metoffice.ini`        |
+-----------------------------------------------------------------------+-----------------------+------------------------------------------------------------+
| `Open Weather Map <http://openweathermap.org/>`_                      | ``openweathermap``    | :download:`../../code/pywws/services/openweathermap.ini`   |
+-----------------------------------------------------------------------+-----------------------+------------------------------------------------------------+
| `Stacja Pogody <http://stacjapogody.waw.pl/index.php?id=mapastacji>`_ | ``stacjapogodywawpl`` | :download:`../../code/pywws/services/stacjapogodywawpl.ini`|
+-----------------------------------------------------------------------+-----------------------+------------------------------------------------------------+
| `temperatur.nu <http://www.temperatur.nu/>`_                          | ``temperaturnu``      | :download:`../../code/pywws/services/temperaturnu.ini`     |
+-----------------------------------------------------------------------+-----------------------+------------------------------------------------------------+
| `Weather Underground <http://www.wunderground.com/>`_                 | ``underground``       | :download:`../../code/pywws/services/underground.ini`      |
+-----------------------------------------------------------------------+-----------------------+------------------------------------------------------------+
| `wetter.com <http://www.wetter.com/community/>`_                      | ``wetterarchivde``    | :download:`../../code/pywws/services/wetterarchivde.ini`   |
+-----------------------------------------------------------------------+-----------------------+------------------------------------------------------------+

Configuration
-------------

If you haven't already done so, visit the organisation's web site and
create an account for your weather station. Make a note of any site ID
and password details you are given.

Stop any pywws software that is running and then run ``toservice.py``
to create a section in ``weather.ini``::

    python pywws/toservice.py data_dir service_name

``service_name`` is a single word service name, such as ``metoffice``,
``data_dir`` is your weather data directory, as usual.

Edit ``weather.ini`` and find the section corresponding to the service
name, e.g. ``[underground]``. Copy your site details into this
section, for example::

    [underground]
    password = secret
    station = ABCDEFG1A

Now you can test your configuration::

    python pywws/toservice.py -vvv data_dir service_name

This should show you the data string that is uploaded. Any failure
should generate an error message.

Upload old data
---------------

Now you can upload your last 7 days' data, if the service supports it.
Edit your ``weather.ini`` file and remove the ``last update`` line
from the appropriate section, then run ``toservice.py`` with the
catchup option::

    python pywws/toservice.py -cvv data_dir service_name

This may take 20 minutes or more, depending on how much data you have.

Add service(s) upload to regular tasks
--------------------------------------

Edit your ``weather.ini`` again, and add a list of services to the
``[live]``, ``[logged]``, ``[hourly]``, ``[12 hourly]`` or ``[daily]``
section, depending on how often you want to send data. For example::

    [live]
    twitter = []
    plot = []
    text = []
    services = ['underground']

    [logged]
    twitter = []
    plot = []
    text = []
    services = ['metoffice', 'stacjapogodywawpl']

    [hourly]
    twitter = []
    plot = []
    text = []
    services = ['underground']

Note that the ``[live]`` section is only used when running
``LiveLog.py``. It is a good idea to repeat any service selected in
``[live]`` in the ``[logged]`` or ``[hourly]`` section in case you
switch to running :mod:`Hourly`.

Restart your regular pywws program (:mod:`Hourly` or :mod:`LiveLog`)
and visit the appropriate web site to see regular updates from your
weather station.

Notes on the services
---------------------

UK Met Office
=============

* Create account: https://register.metoffice.gov.uk/WaveRegistrationClient/public/register.do?service=weatherobservations
* API: http://wow.metoffice.gov.uk/support?category=dataformats#automatic
* Example ``weather.ini`` section::

    [metoffice]
    site id = 12345678
    aws pin = 987654

Open Weather Map
================

* Create account: http://openweathermap.org/login
* API: http://openweathermap.org/API
* Example ``weather.ini`` section::

    [openweathermap]
    lat = 51.501
    long = -0.142
    alt = 10
    user = Elizabeth Windsor
    password = corgi
    id = Buck House

The default behaviour is to use your user name to identify the weather
station. However, it's possible for a user to have more than one
weather station, so there is an undocumented ``name`` parameter in the
API that can be used to identify the station. This appears as ``id``
in ``weather.ini``. Make sure you don't choose a name that is already
in use.

Weather Underground
===================

* Create account: http://www.wunderground.com/members/signup.asp
* API: http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
* Example ``weather.ini`` section::

    [underground]
    station = ABCDEFGH1
    password = xxxxxxx

API
---

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python toservice.py [options] data_dir service_name
 options are:
  -h or --help     display this help
  -c or --catchup  upload all data since last upload
  -v or --verbose  increase amount of reassuring messages
 data_dir is the root directory of the weather data
 service_name is the service to upload to, e.g. underground
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

from ConfigParser import SafeConfigParser
import getopt
import logging
import os
import re
import socket
import sys
import urllib
import urllib2
from datetime import datetime, timedelta

import DataStore
from Logger import ApplicationLogger
import Template

FIVE_MINS = timedelta(minutes=5)

class ToService(object):
    """Upload weather data to weather services such as Weather
    Underground.

    """
    def __init__(self, params, calib_data, service_name=None):
        """

        :param params: pywws configuration.

        :type params: :class:`pywws.DataStore.params`
        
        :param calib_data: 'calibrated' data.

        :type calib_data: :class:`pywws.DataStore.calib_store`

        :keyword service_name: name of service to upload to.

        :type service_name: string
    
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
        socket.setdefaulttimeout(30)
        # open params file
        service_params = SafeConfigParser()
        service_params.optionxform = str
        service_params.readfp(open(os.path.join(
            os.path.dirname(__file__), 'services',
            '%s.ini' % (self.config_section))))
        # get URL
        self.server = service_params.get('config', 'url')
        # get fixed part of upload data
        self.fixed_data = dict()
        for name, value in service_params.items('fixed'):
            if value[0] == '*':
                value = self.params.get(
                    self.config_section, value[1:], 'unknown')
            self.fixed_data[name] = value
        # create templater
        self.templater = Template.Template(
            self.params, self.data, self.data, None, None, use_locale=False)
        self.template_file = os.path.join(
            os.path.dirname(__file__), 'services',
            '%s_template_%s.txt' % (service_name,
                                    self.params.get('fixed', 'ws type')))
        # get other parameters
        self.catchup = eval(service_params.get('config', 'catchup'))
        self.use_get = eval(service_params.get('config', 'use get'))
        rapid_fire = eval(service_params.get('config', 'rapidfire'))
        if rapid_fire:
            self.server_rf = service_params.get('config', 'url-rf')
            self.fixed_data_rf = dict(self.fixed_data)
            for name, value in service_params.items('fixed-rf'):
                self.fixed_data_rf[name] = value
        else:
            self.server_rf = self.server
            self.fixed_data_rf = self.fixed_data
        self.expected_result = eval(service_params.get('config', 'result'))

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
        # convert data
        result = dict(fixed_data)
        template_data = self.templater.make_text(self.template_file, current)
        result.update(eval(template_data))
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
        self.logger.debug(coded_data)
        coded_data = urllib.urlencode(coded_data)
        # have three tries before giving up
        for n in range(3):
            try:
                if sys.hexversion <= 0x020406ff:
                    wudata = urllib.urlopen('%s?%s' % (server, coded_data))
                else:
                    try:
                        if self.use_get:
                            wudata = urllib2.urlopen(
                                '%s?%s' % (server, coded_data))
                        else:
                            wudata = urllib2.urlopen(server, coded_data)
                    except urllib2.HTTPError, ex:
                        if ex.code != 400:
                            raise
                        wudata = ex
                response = wudata.readlines()
                wudata.close()
                if len(response) == len(self.expected_result):
                    for actual, expected in zip(response, self.expected_result):
                        if not re.match(expected, actual):
                            break
                    else:
                        self.old_response = response
                        return True
                if response != self.old_response:
                    for line in response:
                        self.logger.error(line.strip())
                self.old_response = response
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
