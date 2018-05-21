# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2018  pywws contributors

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

"""Upload weather data to MQTT message broker.

MQTT_ is a "message broker" system, typically running on ``localhost``
or another computer in your home network. Use of MQTT with pywws
requires an additional library. See :ref:`Dependencies - MQTT
<dependencies-mqtt>` for details.

* Mosquitto (a lightweight broker): http://mosquitto.org/
* Example ``weather.ini`` configuration::

    [mqtt]
    topic = /weather/pywws
    hostname = localhost
    port = 1883
    client_id = pywws
    retain = False
    user = 
    password = 
    multi_topic = False
    template_txt = ('\\n'
            '#idx          \\'"idx"         : "%Y-%m-%d %H:%M:%S",\\'#\\n'
            '#wind_dir     \\'"wind_dir"    : "%.0f",\\' \\'\\' \\'winddir_degrees(x)\\'#\\n'
            '#wind_ave     \\'"wind_ave"    : "%.2f",\\' \\'\\' \\'wind_mph(x)\\'#\\n'
            '#wind_gust    \\'"wind_gust"   : "%.2f",\\' \\'\\' \\'wind_mph(x)\\'#\\n'
            '#hum_out      \\'"hum_out"     : "%.d",\\'#\\n'
            '#hum_in       \\'"hum_in"      : "%.d",\\'#\\n'
            '#temp_in      \\'"temp_in_c"   : "%.1f",\\'#\\n'
            '#temp_in      \\'"temp_in_f"   : "%.1f",\\' \\'\\' \\'temp_f(x)\\'#\\n'
            '#temp_out     \\'"temp_out_c"  : "%.1f",\\'#\\n'
            '#temp_out     \\'"temp_out_f"  : "%.1f",\\' \\'\\' \\'temp_f(x)\\'#\\n'
            '#rel_pressure \\'"rel_pressure": "%.4f",\\' \\'\\' \\'pressure_inhg(x)\\'#\\n'
            '#calc \\'rain_inch(rain_hour(data))\\' \\'"rainin": "%g",\\'#\\n'
            '#calc \\'rain_inch(rain_day(data))\\' \\'"dailyrainin": "%g",\\'#\\n'
            '#calc \\'rain_hour(data)\\' \\'"rain": "%g",\\'#\\n'
            '#calc \\'rain_day(data)\\' \\'"dailyrain": "%g",\\'#\\n'
            '\\n')

    [logged]
    services = ['mqtt', 'underground']

pywws will publish a JSON string of weather data. This data will be
published to the broker running on ``hostname``, with the port number
specified. (An IP address can be used instead of a host name.)
``client_id`` is a note of who published the data to the topic.
``topic`` can be any string value, this needs to be the topic that a
subscriber is aware of.

``retain`` is a boolean and should be set to ``True`` or ``False``. If
set to ``True`` this will flag the message sent to the broker to be
retained. Otherwise the broker discards the message if no client is
subscribing to this topic. This allows clients to get an immediate
response when they subscribe to a topic, without having to wait until
the next message is published.

``user`` and ``password`` can be used for MQTT authentication.

``multi_topic`` is a boolean and should be set to ``True`` or ``False``.
If set to ``True`` pywws will also publish all the data each as separate
subtopics of the configured ``topic``; e.g., with the ``topic`` set to
/weather/pywws pywws will also publish the outside temperature to
``/weather/pywws/temp_out_c`` and the inside temperature to
``/weather/pywws/temp_in_c``.

``template_txt`` is the template used to generate the data to be
published. You can edit it to suit your own requirements, e.g. not using
antiquated units of measurement. Be very careful about the backslash
escaped quotation marks though.

If these aren't obvious to you it's worth doing a bit of reading around
MQTT. It's a great lightweight messaging system from IBM, recently made
more popular when Facebook published information on their use of it.

This has been tested with the Mosquitto Open Source MQTT broker, running
on a Raspberry Pi (Raspian OS). TLS (mqtt data encryption) is not yet
implemented.

Thanks to Matt Thompson for writing the MQTT code and to Robin Kearney
for adding the retain and auth options.

.. _MQTT: http://mqtt.org/

"""

from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
from datetime import timedelta
import json
import logging
import os
import pprint
import sys

import paho.mqtt.client as mosquitto

import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.BaseToService):
    catchup = 0
    fixed_data = {}
    interval = timedelta(seconds=40)
    logger = logger
    service_name = service_name
    template = """
#idx          '"idx"         : "%Y-%m-%d %H:%M:%S",'#
#wind_dir     '"wind_dir"    : "%.0f",' '' 'winddir_degrees(x)'#
#wind_ave     '"wind_ave"    : "%.2f",' '' 'wind_mph(x)'#
#wind_gust    '"wind_gust"   : "%.2f",' '' 'wind_mph(x)'#
#hum_out      '"hum_out"     : "%.d",'#
#hum_in       '"hum_in"      : "%.d",'#
#temp_in      '"temp_in_c"   : "%.1f",'#
#temp_in      '"temp_in_f"   : "%.1f",' '' 'temp_f(x)'#
#temp_out     '"temp_out_c"  : "%.1f",'#
#temp_out     '"temp_out_f"  : "%.1f",' '' 'temp_f(x)'#
#rel_pressure '"rel_pressure": "%.4f",' '' 'pressure_inhg(x)'#
#calc 'rain_inch(rain_hour(data))' '"rainin": "%g",'#
#calc 'rain_inch(rain_day(data))' '"dailyrainin": "%g",'#
#calc 'rain_hour(data)' '"rain": "%g",'#
#calc 'rain_day(data)' '"dailyrain": "%g",'#

"""

    def __init__(self, context):
        # get configurable data
        self.params = {
            'topic'      : context.params.get(
                service_name, 'topic', '/weather/pywws'),
            'hostname'   : context.params.get(
                service_name, 'hostname', 'localhost'),
            'port'       : eval(context.params.get(
                service_name, 'port', '1883')),
            'client_id'  : context.params.get(
                service_name, 'client_id', 'pywws'),
            'retain'     : eval(context.params.get(
                service_name, 'retain', 'False')),
            'user'       : context.params.get(service_name, 'user', ''),
            'password'   : context.params.get(service_name, 'password', ''),
            'multi_topic': eval(context.params.get(
                service_name, 'multi_topic', 'False')),
            }
        # get template text
        template = eval(context.params.get(
            service_name, 'template_txt', pprint.pformat(self.template)))
        logger.log(logging.DEBUG - 1, 'template:\n' + template)
        self.template = "#live#" + template
        # base class init
        super(ToService, self).__init__(context)

    @contextmanager
    def session(self):
        session = mosquitto.Client(
            self.params['client_id'], protocol=mosquitto.MQTTv31)
        if self.params['password']:
            session.username_pw_set(
                self.params['user'], self.params['password'])
        elif self.params['user']:
            session.username_pw_set(self.params['user'])
        logger.debug(('connecting to host {hostname:s}:{port:d} '
                      'with client_id "{client_id:s}"').format(**self.params))
        session.connect(self.params['hostname'], self.params['port'])
        try:
            yield session
        finally:
            session.disconnect()

    def upload_data(self, session, prepared_data={}, live=False):
        logger.debug((
            'publishing on topic "{topic:s}" with retain={retain!s},'
            ' data="{data!r}"').format(data=prepared_data, **self.params))
        try:
            session.publish(self.params['topic'], json.dumps(prepared_data),
                            retain=self.params['retain'])
        except Exception as ex:
            return False, str(ex)
        if self.params['multi_topic']:
            # Publish messages, one for each item in prepared_data to
            # separate Subtopics.
            for key, value in prepared_data.items():
                if value == '':
                    value = 'None'
                try:
                    session.publish(self.params['topic'] + "/" + key, value,
                                    retain=self.params['retain'])
                except Exception as ex:
                    return False, str(ex)
            # Need to make sure the messages have been flushed to the
            # server.
            session.loop(timeout=0.5) 
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
