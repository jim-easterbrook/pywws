#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

+-----------------------------------------------------------------------+-----------------------+-------------------------------------------------------+
| organisation                                                          | service name          | config file                                           |
+=======================================================================+=======================+=======================================================+
| `UK Met Office <http://wow.metoffice.gov.uk/>`_                       | ``metoffice``         | :download:`../../pywws/services/metoffice.ini`        |
+-----------------------------------------------------------------------+-----------------------+-------------------------------------------------------+
| `Open Weather Map <http://openweathermap.org/>`_                      | ``openweathermap``    | :download:`../../pywws/services/openweathermap.ini`   |
+-----------------------------------------------------------------------+-----------------------+-------------------------------------------------------+
| `PWS Weather <www.pwsweather.com>`_                                   | ``pwsweather``        | :download:`../../pywws/services/pwsweather.ini`       |
+-----------------------------------------------------------------------+-----------------------+-------------------------------------------------------+
| `Stacja Pogody <http://stacjapogody.waw.pl/index.php?id=mapastacji>`_ | ``stacjapogodywawpl`` | :download:`../../pywws/services/stacjapogodywawpl.ini`|
+-----------------------------------------------------------------------+-----------------------+-------------------------------------------------------+
| `temperatur.nu <http://www.temperatur.nu/>`_                          | ``temperaturnu``      | :download:`../../pywws/services/temperaturnu.ini`     |
+-----------------------------------------------------------------------+-----------------------+-------------------------------------------------------+
| `Weather Underground <http://www.wunderground.com/>`_                 | ``underground``       | :download:`../../pywws/services/underground.ini`      |
+-----------------------------------------------------------------------+-----------------------+-------------------------------------------------------+
| `wetter.com <http://www.wetter.com/community/>`_                      | ``wetterarchivde``    | :download:`../../pywws/services/wetterarchivde.ini`   |
+-----------------------------------------------------------------------+-----------------------+-------------------------------------------------------+

Configuration
-------------

If you haven't already done so, visit the organisation's web site and
create an account for your weather station. Make a note of any site ID
and password details you are given.

Stop any pywws software that is running and then run ``toservice`` to
create a section in ``weather.ini``::

    python -m pywws.toservice data_dir service_name

``service_name`` is a single word service name, such as ``metoffice``,
``data_dir`` is your weather data directory, as usual.

Edit ``weather.ini`` and find the section corresponding to the service
name, e.g. ``[underground]``. Copy your site details into this
section, for example::

    [underground]
    password = secret
    station = ABCDEFG1A

Now you can test your configuration::

    python -m pywws.toservice -vvv data_dir service_name

This should show you the data string that is uploaded. Any failure
should generate an error message.

Upload old data
---------------

Now you can upload your last 7 days' data, if the service supports it.
Edit your ``status.ini`` file and remove the appropriate line from the
``last update`` section, then run ``toservice`` with the catchup
option::

    python -m pywws.toservice -cvv data_dir service_name

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
    services = ['underground_rf']

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
:py:mod:`~pywws.LiveLog`. It is a good idea to repeat any service
selected in ``[live]`` in the ``[logged]`` or ``[hourly]`` section in
case you switch to running :py:mod:`~pywws.Hourly`.

Restart your regular pywws program (:py:mod:`~pywws.Hourly` or
:py:mod:`~pywws.LiveLog`) and visit the appropriate web site to see
regular updates from your weather station.

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

PWS Weather
===================

* Create account: http://www.pwsweather.com/register.php
* API based on WU protocol: `<http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol>`_
* Example ``weather.ini`` section::

    [pwsweather]
    station = ABCDEFGH1
    password = xxxxxxx

Weather Underground
===================

* Create account: http://www.wunderground.com/members/signup.asp
* API: `<http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol>`_
* Example ``weather.ini`` section::

    [underground]
    station = ABCDEFGH1
    password = xxxxxxx

API
---

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.toservice [options] data_dir service_name
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

from pywws import DataStore
from pywws.Logger import ApplicationLogger
from pywws import Template

FIVE_MINS = timedelta(minutes=5)

class ToService(object):
    """Upload weather data to weather services such as Weather
    Underground.

    """
    def __init__(self, params, status, calib_data, service_name):
        """

        :param params: pywws configuration.

        :type params: :class:`pywws.DataStore.params`
        
        :param status: pywws status store.

        :type status: :class:`pywws.DataStore.status`
        
        :param calib_data: 'calibrated' data.

        :type calib_data: :class:`pywws.DataStore.calib_store`

        :param service_name: name of service to upload to.

        :type service_name: string
    
        """
        self.logger = logging.getLogger('pywws.ToService(%s)' % service_name)
        self.params = params
        self.status = status
        self.data = calib_data
        self.service_name = service_name
        # 'derived' services such as 'underground_rf' share their
        # parent's config and templates
        config_section = self.service_name.split('_')[0]
        self.old_response = None
        self.old_ex = None
        # set default socket timeout, so urlopen calls don't hang forever
        socket.setdefaulttimeout(30)
        # open params file
        service_params = SafeConfigParser()
        service_params.optionxform = str
        service_params.readfp(open(os.path.join(
            os.path.dirname(__file__), 'services', '%s.ini' % (self.service_name))))
        # get URL
        self.server = service_params.get('config', 'url')
        # get fixed part of upload data
        self.fixed_data = dict()
        for name, value in service_params.items('fixed'):
            if value[0] == '*':
                value = self.params.get(config_section, value[1:], 'unknown')
            self.fixed_data[name] = value
        # create templater
        self.templater = Template.Template(
            self.params, self.status, self.data, self.data, None, None,
            use_locale=False)
        self.template_file = os.path.join(
            os.path.dirname(__file__), 'services', '%s_template_%s.txt' % (
                config_section, self.params.get('config', 'ws type')))
        # get other parameters
        self.catchup = eval(service_params.get('config', 'catchup'))
        self.use_get = eval(service_params.get('config', 'use get'))
        self.expected_result = eval(service_params.get('config', 'result'))

    def encode_data(self, data):
        """Encode a weather data record.

        The :obj:`data` parameter contains the data to be encoded. It
        should be a 'calibrated' data record, as stored in
        :class:`pywws.DataStore.calib_store`.

        :param data: the weather data record.

        :type data: dict

        :return: urlencoded data.

        :rtype: string
        
        """
        # check we have enough data
        if data['temp_out'] is None or data['hum_out'] is None:
            return None
        # convert data
        coded_data = eval(self.templater.make_text(self.template_file, data))
        coded_data.update(self.fixed_data)
        return urllib.urlencode(coded_data)

    def send_data(self, coded_data):
        """Upload a weather data record.

        The :obj:`coded_data` parameter contains the data to be uploaded.
        It should be a urlencoded string.

        :param coded_data: the data to upload.

        :type data: string

        :return: success status

        :rtype: bool
        
        """
        self.logger.debug(coded_data)
        # have three tries before giving up
        for n in range(3):
            try:
                try:
                    if self.use_get:
                        wudata = urllib2.urlopen(
                            '%s?%s' % (self.server, coded_data))
                    else:
                        wudata = urllib2.urlopen(self.server, coded_data)
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

    def next_data(self, start, live_data):
        """Get weather data records to upload.

        This method returns either the most recent weather data
        record, or all records since a given datetime, according to
        the value of :obj:`start`.

        :param start: datetime of first record to get, or None to get
         most recent data only.

        :type start: datetime

        :param live_data: a current 'live' data record, or None.

        :type live_data: dict

        :return: yields weather data records.

        :rtype: dict
        
        """
        if live_data:
            yield live_data
        elif start:
            for data in self.data[start:]:
                yield data
        else:
            # use most recent logged data
            yield self.data[self.data.before(datetime.max)]

    def catchup_start(self):
        """Get datetime of first 'catchup' record to send.

        :rtype: datetime

        """
        if self.catchup <= 0:
            return None
        start = datetime.utcnow() - timedelta(days=self.catchup)
        last_update = self.params.get_datetime(self.service_name, 'last update')
        if last_update:
            self.params.unset(self.service_name, 'last update')
            self.status.set('last update', self.service_name,
                            last_update.isoformat(' '))
        last_update = self.status.get_datetime('last update', self.service_name)
        if last_update:
            start = max(start, last_update + timedelta(seconds=30))
        return start

    def Upload(self, catchup, live_data=None):
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
        if catchup:
            start = self.catchup_start()
        else:
            start = None
        count = 0
        for data in self.next_data(start, live_data):
            coded_data = self.encode_data(data)
            if not coded_data:
                continue
            if not self.send_data(coded_data):
                return False
            self.status.set('last update', self.service_name,
                            data['idx'].isoformat(' '))
            count += 1
        if count > 1:
            self.logger.info('%d records sent', count)
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
        DataStore.params(args[0]), DataStore.status(args[0]),
        DataStore.calib_store(args[0]), args[1]).Upload(catchup)

if __name__ == "__main__":
    sys.exit(main())
