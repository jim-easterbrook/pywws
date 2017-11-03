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

"""Post weather update to services such as Weather Underground
::

%s

Introduction
------------

There are an increasing number of web sites around the world that
encourage amateur weather station owners to upload data over the
internet.

This module enables pywws to upload readings to these organisations.
It is highly customisable using configuration files. Each 'service'
requires a configuration file and one or two templates in
``pywws/services`` (that should not need to be edited by the user) and
a section in ``weather.ini`` containing user specific data such as
your site ID and password.

See :ref:`How to integrate pywws with various weather services
<guides-integration-other>` for details of the available services.

Configuration
-------------

If you haven't already done so, visit the organisation's web site and
create an account for your weather station. Make a note of any site ID
and password details you are given.

Stop any pywws software that is running and then run ``toservice`` to
create a section in ``weather.ini``::

    python -m pywws.toservice data_dir service_name

``service_name`` is the single word service name used by pywws, such
as ``metoffice``, ``data_dir`` is your weather data directory, as
usual.

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
Run ``toservice`` with the catchup option::

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
    services = ['underground_rf', 'cwop']

    [logged]
    twitter = []
    plot = []
    text = []
    services = ['metoffice', 'cwop']

    [hourly]
    twitter = []
    plot = []
    text = []
    services = ['underground']

Note that the ``[live]`` section is only used when running
:py:mod:`pywws.LiveLog`. It is a good idea to repeat any
service selected in ``[live]`` in the ``[logged]`` or ``[hourly]``
section in case you switch to running :py:mod:`pywws.Hourly`.

Restart your regular pywws program (:py:mod:`pywws.Hourly` or
:py:mod:`pywws.LiveLog`) and visit the appropriate web site to
see regular updates from your weather station.

Using a different template
--------------------------

For some services (mainly MQTT) you might want to write your own
template to give greater control over the uploaded data. Copy the
default template file from ``pywws/services`` to your template directory
and then edit it to do what you want. Now edit ``weather.ini`` and
change the ``template`` value from ``default`` to the name of your
custom template.

API
---

"""

from __future__ import absolute_import

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

import base64
from ConfigParser import SafeConfigParser
from datetime import datetime, timedelta
import getopt
import logging
import os
import pkg_resources
import re
import socket
import StringIO
import sys
import urllib
import urllib2
import urlparse

from pywws import DataStore
from pywws.Logger import ApplicationLogger
from pywws import Template
from pywws import __version__

PARENT_MARGIN = timedelta(minutes=2)

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
        if config_section == self.service_name:
            self.parent = None
        else:
            self.parent = config_section
        self.old_response = None
        self.old_ex = None
        self.http_headers = None
        # set default socket timeout, so urlopen calls don't hang forever
        if eval(self.params.get('config', 'asynchronous', 'False')):
            socket.setdefaulttimeout(60)
        else:
            socket.setdefaulttimeout(20)
        # open params file
        service_params = SafeConfigParser()
        service_params.optionxform = str
        param_string = pkg_resources.resource_string(
            'pywws', 'services/%s.ini' % (self.service_name))
        if sys.version_info[0] >= 3:
            param_string = param_string.decode('utf-8')
        service_params.readfp(StringIO.StringIO(param_string))
        # get URL
        self.server = service_params.get('config', 'url')
        parsed_url = urlparse.urlsplit(self.server)
        if parsed_url.scheme == 'aprs':
            self.send_data = self.aprs_send_data
            server, port = parsed_url.netloc.split(':')
            self.server = (server, int(port))
        elif parsed_url.scheme == 'mqtt':
            self.send_data = self.mqtt_send_data
        else:
            self.send_data = self.http_send_data
            self.use_get = eval(service_params.get('config', 'use get'))
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
        template_name = self.params.get(config_section, 'template', 'default')
        if template_name != 'default':
            template_dir = self.params.get(
                'paths', 'templates', os.path.expanduser('~/weather/templates/'))
            self.template_file = open(
                os.path.join(template_dir, template_name), 'rb')
        else:
            template_name = 'services/%s_template_%s.txt' % (
                config_section, self.params.get('config', 'ws type'))
            if not pkg_resources.resource_exists('pywws', template_name):
                template_name = 'services/%s_template_1080.txt' % (config_section)
            self.template_file = pkg_resources.resource_stream(
                'pywws', template_name)
        # get other parameters
        self.auth_type = service_params.get('config', 'auth_type')
        if self.auth_type == 'basic':
            user = self.params.get(config_section, 'user', 'unknown')
            password = self.params.get(config_section, 'password', 'unknown')
            details = user + ':' + password
            self.auth = 'Basic ' + base64.b64encode(details.encode('utf-8')).decode('utf-8')
        elif self.auth_type == 'mqtt':
            self.user = self.params.get(config_section, 'user', 'unknown')
            self.password = self.params.get(config_section, 'password', 'unknown')
        self.catchup = eval(service_params.get('config', 'catchup'))
        self.expected_result = eval(service_params.get('config', 'result'))
        self.interval = eval(service_params.get('config', 'interval'))
        self.interval = max(self.interval, 40)
        self.interval = timedelta(seconds=self.interval)
        if service_params.has_option('config', 'http_headers'):
            self.http_headers = eval(service_params.get('config', 'http_headers'))
        # move 'last update' from params to status
        last_update = self.params.get_datetime(self.service_name, 'last update')
        if last_update:
            self.params.unset(self.service_name, 'last update')
            self.status.set(
                'last update', self.service_name, last_update.isoformat(' '))
        # set timestamp of first data to upload
        self.next_update = datetime.utcnow() - max(
            timedelta(days=self.catchup), self.interval)
        self.next_update = min(self.next_update, self.data.before(datetime.max))

    def prepare_data(self, data):
        """Prepare a weather data record.

        The :obj:`data` parameter contains the data to be encoded. It
        should be a 'calibrated' data record, as stored in
        :class:`pywws.DataStore.calib_store`. The relevant data items
        are extracted and converted to strings using a template, then
        merged with the station's "fixed" data.

        :param data: the weather data record.

        :type data: dict

        :return: dict.

        :rtype: string

        """
        # check we have external data
        if data['temp_out'] is None:
            return None
        # convert data
        data_str = self.templater.make_text(self.template_file, data)
        self.template_file.seek(0)
        if not data_str:
            return None
        prepared_data = eval(data_str)
        prepared_data.update(self.fixed_data)
        return prepared_data

    def mqtt_send_data(self, timestamp, prepared_data, ignore_last_update=False):
        import paho.mqtt.client as mosquitto
        import time
        import json

        topic = prepared_data['topic']
        hostname = prepared_data['hostname']
        port = prepared_data['port']
        client_id = prepared_data['client_id']
        retain = prepared_data['retain'] == 'True'
        auth = prepared_data['auth'] == 'True'
        multi_topic = prepared_data['multi_topic'] == 'True'
        # clean up the object
        del prepared_data['topic']
        del prepared_data['hostname']
        del prepared_data['port']
        del prepared_data['client_id']
        del prepared_data['retain']
        del prepared_data['auth']
        del prepared_data['multi_topic']

        mosquitto_client = mosquitto.Client(client_id, protocol=mosquitto.MQTTv31)
        if auth:
            self.logger.debug("Username and password configured")
            if(self.password == "unknown"):
                mosquitto_client.username_pw_set(self.user)
            else:
                mosquitto_client.username_pw_set(self.user, self.password)
        else:
            self.logger.debug("Username and password unconfigured, ignoring")
        self.logger.debug(
            "timestamp: %s. publishing on topic [%s] to hostname [%s] and " +
            "port [%s] with a client_id [%s] and retain is %s",
            timestamp.isoformat(' '), topic, hostname, port, client_id, retain)

        mosquitto_client.connect(hostname, int(port))
        mosquitto_client.publish(topic, json.dumps(prepared_data), retain=retain)

        if multi_topic:
            #Publish a messages, one for each item in prepared_data to separate Subtopics. 
            for item in prepared_data:
                if prepared_data[item] == '':
                    prepared_data[item] = 'None'
                mosquitto_client.publish(topic + "/" + item, prepared_data[item], retain=retain)
            #Need to make sure the messages have been flushed to the server.
            mosquitto_client.loop(timeout=0.5) 

        self.logger.debug("published data: %s", prepared_data)
        mosquitto_client.disconnect()
        return True

    def aprs_send_data(self, timestamp, prepared_data, ignore_last_update=False):
        """Upload a weather data record using APRS.

        The :obj:`prepared_data` parameter contains the data to be uploaded.
        It should be a dictionary of string keys and string values.

        :param timestamp: the timestamp of the data to upload.

        :type timestamp: datetime

        :param prepared_data: the data to upload.

        :type prepared_data: dict

        :param ignore_last_update: don't get or set the 'last update'
            status.ini entry.

        :type ignore_last_update: bool

        :return: success status

        :rtype: bool

        """

        login = 'user %s pass %s vers pywws %s\n' % (
            prepared_data['designator'], prepared_data['passcode'], __version__)
        packet = '%s>APRS,TCPIP*:@%sz%s/%s_%s/%sg%st%sr%sP%sb%sh%s.pywws-%s\n' % (
            prepared_data['designator'],   prepared_data['idx'],
            prepared_data['latitude'],     prepared_data['longitude'],
            prepared_data['wind_dir'],     prepared_data['wind_ave'],
            prepared_data['wind_gust'],    prepared_data['temp_out'],
            prepared_data['rain_hour'],    prepared_data['rain_day'],
            prepared_data['rel_pressure'], prepared_data['hum_out'],
            __version__
            )
        self.logger.debug('packet: "%s"', packet)
        login = login.encode('ASCII')
        packet = packet.encode('ASCII')
        sock = socket.socket()
        try:
            sock.connect(self.server)
            try:
                response = sock.recv(4096)
                self.logger.debug('server software: %s', response.strip())
                sock.sendall(login)
                response = sock.recv(4096)
                self.logger.debug('server login ack: %s', response.strip())
                sock.sendall(packet)
                sock.shutdown(socket.SHUT_RDWR)
            finally:
                sock.close()
        except Exception, ex:
            new_ex = str(ex)
            if new_ex == self.old_ex:
                log = self.logger.debug
            else:
                log = self.logger.error
                self.old_ex = new_ex
            log('exc: %s', new_ex)
            return False
        if not ignore_last_update:
            self.set_last_update(timestamp)
        return True

    def http_send_data(self, timestamp, prepared_data, ignore_last_update=False):
        """Upload a weather data record using HTTP.

        The :obj:`prepared_data` parameter contains the data to be uploaded.
        It should be a dictionary of string keys and string values.

        :param timestamp: the timestamp of the data to upload.

        :type timestamp: datetime

        :param prepared_data: the data to upload.

        :type prepared_data: dict

        :param ignore_last_update: don't get or set the 'last update'
            status.ini entry.

        :type ignore_last_update: bool

        :return: success status

        :rtype: bool

        """
        coded_data = urllib.urlencode(prepared_data)
        self.logger.debug(coded_data)
        new_ex = self.old_ex
        ex_info = []
        success = False
        try:
            if self.use_get:
                request = urllib2.Request(self.server + '?' + coded_data)
            else:
                request = urllib2.Request(self.server, coded_data.encode('ASCII'))
            if self.auth_type == 'basic':
                request.add_header('Authorization', self.auth)
            if self.http_headers is not None:
                for header in self.http_headers:
                    request.add_header(header[0], header[1])
            rsp = urllib2.urlopen(request)
            response = rsp.readlines()
            rsp.close()
            if response == self.old_response:
                log = self.logger.debug
            else:
                log = self.logger.error
                self.old_response = response
            for line in response:
                log('rsp: %s', line.strip())
            for n, expected in enumerate(self.expected_result):
                if n < len(response):
                    actual = response[n].decode('utf-8')
                    if not re.match(expected, actual):
                        break
            else:
                self.old_response = response
                if not ignore_last_update:
                    self.set_last_update(timestamp)
                return True
            return False
        except urllib2.HTTPError, ex:
            if ex.code == 429 and self.service_name == 'metoffice':
                # UK Met Office server uses 429 to signal duplicate data
                success = True
            if sys.version_info >= (2, 7):
                new_ex = '[%d]%s' % (ex.code, ex.reason)
            else:
                new_ex = str(ex)
            ex_info = str(ex.info()).split('\n')
            try:
                for line in ex.readlines():
                    line = line.decode('utf-8')
                    ex_info.append(re.sub('<.+?>', '', line))
            except Exception:
                pass
        except urllib2.URLError, ex:
            new_ex = str(ex.reason)
        except Exception, ex:
            new_ex = str(ex)
        if new_ex == self.old_ex:
            log = self.logger.debug
        else:
            log = self.logger.error
            self.old_ex = new_ex
        log('exc: %s', new_ex)
        for extra in ex_info:
            extra = extra.strip()
            if extra:
                log('info: %s', extra)
        if success and not ignore_last_update:
            self.set_last_update(timestamp)
        return success

    def next_data(self, catchup, live_data, ignore_last_update=False):
        """Get weather data records to upload.

        This method returns either the most recent weather data
        record, or all records since the last upload, according to
        the value of :obj:`catchup`.

        :param catchup: ``True`` to get all records since last upload,
         or ``False`` to get most recent data only.

        :type catchup: boolean

        :param live_data: a current 'live' data record, or ``None``.

        :type live_data: dict

        :param ignore_last_update: don't get the 'last update'
            status.ini entry.

        :type ignore_last_update: bool

        :return: yields weather data records.

        :rtype: dict

        """
        if ignore_last_update:
            last_update = None
        else:
            last_update = self.status.get_datetime(
                'last update', self.service_name)
        if last_update:
            self.next_update = max(self.next_update,
                                   last_update + self.interval)
        if catchup:
            start = self.next_update
        else:
            start = self.data.before(datetime.max)
        if live_data:
            stop = live_data['idx'] - self.interval
        else:
            stop = None
        for data in self.data[start:stop]:
            if data['idx'] >= self.next_update:
                self.next_update = data['idx'] + self.interval
                yield data
        if live_data and live_data['idx'] >= self.next_update:
            self.next_update = live_data['idx'] + self.interval
            yield live_data

    def set_last_update(self, timestamp):
        self.status.set(
            'last update', self.service_name, timestamp.isoformat(' '))
        if self.parent:
            last_update = self.status.get_datetime('last update', self.parent)
            if last_update and last_update >= timestamp - PARENT_MARGIN:
                self.status.set('last update', self.parent,
                                (timestamp + PARENT_MARGIN).isoformat(' '))

    def Upload(self, catchup=True, live_data=None, ignore_last_update=False):
        """Upload one or more weather data records.

        This method uploads either the most recent weather data
        record, or all records since the last upload (up to 7 days),
        according to the value of :obj:`catchup`.

        It sets the ``last update`` configuration value to the time
        stamp of the most recent record successfully uploaded.

        :param catchup: upload all data since last upload.

        :type catchup: bool

        :param live_data: current 'live' data. If not present the most
            recent logged data is uploaded.

        :type live_data: dict

        :param ignore_last_update: don't get or set the 'last update'
            status.ini entry.

        :type ignore_last_update: bool

        :return: success status

        :rtype: bool

        """
        count = 0
        for data in self.next_data(catchup, live_data, ignore_last_update):
            prepared_data = self.prepare_data(data)
            if not prepared_data:
                continue
            if not self.send_data(data['idx'], prepared_data, ignore_last_update):
                return False
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
        DataStore.calib_store(args[0]), args[1]).Upload(
            catchup=catchup, ignore_last_update=not catchup)

if __name__ == "__main__":
    sys.exit(main())
