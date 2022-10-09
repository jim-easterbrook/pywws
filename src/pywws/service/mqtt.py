# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2018-22  pywws contributors

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
    tls_cert = /home/pi/pywws/ca_cert/mqtt_ca.crt
    tls_ver = 2
    multi_topic = False

    [logged]
    services = ['mqtt', 'underground']

* To customize the MQTT message use template_txt (remove illuminance and uv if weather station does not support them)::

    [mqtt]
    ... (as above)
    template_txt = ('\\n'
            '#idx          \\'"idx"         : "%Y-%m-%d %H:%M:%S",\\'#\\n'
            '#wind_dir     \\'"wind_dir_degrees"    : "%.d",\\' \\'\\' \\'winddir_degrees(x)\\'#\\n'
            '#wind_dir     \\'"wind_dir_text"       : "%s",\\' \\'\\' \\'winddir_text(x)\\'#\\n'
            '#wind_ave     \\'"wind_ave_mps"    : "%.2f",\\'#\\n'
            '#wind_ave     \\'"wind_ave_mph"    : "%.2f",\\' \\'\\' \\'wind_mph(x)\\'#\\n'
            '#wind_gust    \\'"wind_gust_mps"   : "%.2f",\\'#\\n'
            '#wind_gust    \\'"wind_gust_mph"   : "%.2f",\\' \\'\\' \\'wind_mph(x)\\'#\\n'
            '#calc \\'wind_chill(data["temp_out"],data["wind_ave"])\\' \\'"wind_chill_c" : "%.1f",\\'#\\n'
            '#calc \\'temp_f(wind_chill(data["temp_out"],data["wind_ave"]))\\' \\'"wind_chill_f" : "%.1f",\\'#\\n'
            '#calc \\'dew_point(data["temp_out"],data["hum_out"])\\' \\'"dew_point_c" : "%.1f",\\'#\\n'
            '#calc \\'temp_f(dew_point(data["temp_out"],data["hum_out"]))\\' \\'"dew_point_f" : "%.1f",\\'#\\n'
            '#hum_out      \\'"hum_out"     : "%.d",\\'#\\n'
            '#hum_in       \\'"hum_in"      : "%.d",\\'#\\n'
            '#temp_in      \\'"temp_in_c"   : "%.1f",\\'#\\n'
            '#temp_in      \\'"temp_in_f"   : "%.1f",\\' \\'\\' \\'temp_f(x)\\'#\\n'
            '#temp_out     \\'"temp_out_c"  : "%.1f",\\'#\\n'
            '#temp_out     \\'"temp_out_f"  : "%.1f",\\' \\'\\' \\'temp_f(x)\\'#\\n'
            '#calc \\'apparent_temp(data["temp_out"],data["hum_out"],data["wind_ave"])\\' \\'"temp_out_realfeel_c" : "%.1f",\\'#\\n'
            '#calc \\'temp_f(apparent_temp(data["temp_out"],data["hum_out"],data["wind_ave"]))\\' \\'"temp_out_realfeel_f" : "%.1f",\\'#\\n'
            '#rel_pressure \\'"pressure_rel_hpa": "%.1f",\\'#\\n'
            '#rel_pressure \\'"pressure_rel_inhg": "%.4f",\\' \\'\\' \\'pressure_inhg(x)\\'#\\n'
            '#abs_pressure \\'"pressure_abs_hpa": "%.1f",\\'#\\n'
            '#abs_pressure \\'"pressure_abs_inhg": "%.4f",\\' \\'\\' \\'pressure_inhg(x)\\'#\\n'
            '#rain         \\'"rain_mm"     : "%.1f",\\'#\\n'
            '#rain         \\'"rain_in"     : "%.2f",\\' \\'\\' \\'rain_inch(x)\\'#\\n'
            '#calc \\'rain_hour(data)\\' \\'"rain_last_hour_mm": "%.1f",\\'#\\n'
            '#calc \\'rain_inch(rain_hour(data))\\' \\'"rain_last_hour_in": "%.2f",\\'#\\n'
            '#calc \\'rain_24hr(data)\\' \\'"rain_last_24hours_mm": "%.1f",\\'#\\n'
            '#calc \\'rain_inch(rain_24hr(data))\\' \\'"rain_last_24hours_in": "%.2f",\\'#\\n'
            '#calc \\'rain_day(data)\\' \\'"rain_day_mm": "%.1f",\\'#\\n'
            '#calc \\'rain_inch(rain_day(data))\\' \\'"rain_day_in": "%.2f",\\'#\\n'
            '#illuminance  \\'"illuminance_lux" : "%.1f",\\'#\\n'
            '#illuminance  \\'"illuminance_wm2" : "%.2f",\\' \\'\\' \\'illuminance_wm2(x)\\'#\\n'
            '#uv           \\'"uv"          : "%.d",\\'#\\n'
            '\\n')

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

``tls_cert`` and ``tls_ver`` are used for MQTT TLS security. Set
tls_cert as the path to a CA certificate (e.g. tls_cert =
/home/pi/pywws/ca_cert/mqtt_ca.crt) and tls_ver to the TLS version (e.g.
tls_ver = 2) (TLS1.2 recommended). See
https://mosquitto.org/man/mosquitto-tls-7.html for information on how to
generate certificates. Only copy the ca.crt to your pywws client. See
http://www.steves-internet-guide.com/mosquitto-tls/ for a step-by-step
guide to securing your MQTT server. Note that secure MQTTS usually uses
port 8883, so you will need to also change the port number.

``multi_topic`` is a boolean and should be set to ``True`` or ``False``.
If set to ``True`` pywws will also publish all the data each as separate
subtopics of the configured ``topic``; e.g., with the ``topic`` set to
/weather/pywws pywws will also publish the outside temperature to
``/weather/pywws/temp_out_c`` and the inside temperature to
``/weather/pywws/temp_in_c``.

``template_txt`` is the template used to generate the data to be
published. You can edit it to suit your own requirements. Be very careful
about the backslash escaped quotation marks though. If not specified
default will be used, which sends a lot of values in metric and imperial
units.

.. versionchanged:: 19.5.0
   Default for ``template_txt`` was updated. This change is not backwards
   compatible, the original values are still present, just under new names.
   New default tries to send most of the values pywws collects in both
   metric and imperial units. This is to make it easier for new users
   to get going.

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

from ast import literal_eval
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


class ToService(pywws.service.LiveDataService):
    config = {
        'topic'      : ('/weather/pywws', True,  None),
        'hostname'   : ('localhost',      True,  None),
        'port'       : ('1883',           True,  None),
        'client_id'  : ('pywws',          True,  None),
        'retain'     : ('False',          True,  None),
        'user'       : ('',               False, None),
        'password'   : ('',               False, None),
        'tls_cert'   : ('',               False, None),
        'tls_ver'    : ('1',              True,  None),
        'multi_topic': ('False',          True,  None),
        }
    logger = logger
    service_name = service_name
    template = """
#idx          '"idx"             : "%Y-%m-%d %H:%M:%S",'#
#wind_dir     '"wind_dir_degrees": "%.d",' '' 'winddir_degrees(x)'#
#wind_dir     '"wind_dir_text"   : "%s",' '' 'winddir_text(x)'#
#wind_ave     '"wind_ave_mps"    : "%.2f",'#
#wind_ave     '"wind_ave_mph"    : "%.2f",' '' 'wind_mph(x)'#
#wind_gust    '"wind_gust_mps"   : "%.2f",'#
#wind_gust    '"wind_gust_mph"   : "%.2f",' '' 'wind_mph(x)'#
#calc 'wind_chill(data["temp_out"],data["wind_ave"])'         '"wind_chill_c" : "%.1f",'#
#calc 'temp_f(wind_chill(data["temp_out"],data["wind_ave"]))' '"wind_chill_f" : "%.1f",'#
#calc 'dew_point(data["temp_out"],data["hum_out"])'           '"dew_point_c" : "%.1f",'#
#calc 'temp_f(dew_point(data["temp_out"],data["hum_out"]))'   '"dew_point_f" : "%.1f",'#
#hum_out      '"hum_out"     : "%.d",'#
#hum_in       '"hum_in"      : "%.d",'#
#temp_in      '"temp_in_c"   : "%.1f",'#
#temp_in      '"temp_in_f"   : "%.1f",' '' 'temp_f(x)'#
#temp_out     '"temp_out_c"  : "%.1f",'#
#temp_out     '"temp_out_f"  : "%.1f",' '' 'temp_f(x)'#
#calc 'apparent_temp(data["temp_out"],data["hum_out"],data["wind_ave"])'         '"temp_out_realfeel_c" : "%.1f",'#
#calc 'temp_f(apparent_temp(data["temp_out"],data["hum_out"],data["wind_ave"]))' '"temp_out_realfeel_f" : "%.1f",'#
#rel_pressure '"pressure_rel_hpa" : "%.1f",'#
#rel_pressure '"pressure_rel_inhg": "%.4f",' '' 'pressure_inhg(x)'#
#abs_pressure '"pressure_abs_hpa" : "%.1f",'#
#abs_pressure '"pressure_abs_inhg": "%.4f",' '' 'pressure_inhg(x)'#
#rain         '"rain_mm"     : "%.1f",'#
#rain         '"rain_in"     : "%.2f",' '' 'rain_inch(x)'#
#calc 'rain_hour(data)'            '"rain_last_hour_mm": "%.1f",'#
#calc 'rain_inch(rain_hour(data))' '"rain_last_hour_in": "%.2f",'#
#calc 'rain_24hr(data)'            '"rain_last_24hours_mm": "%.1f",'#
#calc 'rain_inch(rain_24hr(data))' '"rain_last_24hours_in": "%.2f",'#
#calc 'rain_day(data)'             '"rain_day_mm": "%.1f",'#
#calc 'rain_inch(rain_day(data))'  '"rain_day_in": "%.2f",'#
"""
    template_3080_add = """
#illuminance  '"illuminance_lux" : "%.1f",'#
#illuminance  '"illuminance_wm2" : "%.2f",' '' 'illuminance_wm2(x)'#
#uv           '"uv"          : "%.d",'#
"""

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        # extend template
        if context.params.get('config', 'ws type') == '3080':
            self.template += self.template_3080_add
        # get template text
        template = literal_eval(context.params.get(
            service_name, 'template_txt', self.template_format(self.template)))
        logger.log(logging.DEBUG - 1, 'template:\n' + template)
        self.template = "#live#" + template
        # convert some params from string
        for key in ('port', 'retain', 'tls_ver', 'multi_topic'):
            self.params[key] = literal_eval(self.params[key])

    def template_format(self, template):
        result = []
        for line in template.splitlines():
            if line:
                result.append(pprint.pformat(line, width=256))
        return '(\n' + '\n'.join(result) + '\n)'

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
        if self.params['tls_cert']:
            session.tls_set(self.params['tls_cert'], tls_version=self.params['tls_ver'])
        session.connect(self.params['hostname'], self.params['port'])
        try:
            yield session, 'OK'
        finally:
            session.disconnect()

    def upload_data(self, session, prepared_data={}):
        logger.debug((
            'publishing on topic "{topic:s}" with retain={retain!s},'
            ' data="{data!r}"').format(data=prepared_data, **self.params))
        try:
            session.publish(self.params['topic'], json.dumps(prepared_data),
                            retain=self.params['retain'])
        except Exception as ex:
            return False, repr(ex)
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
                    return False, repr(ex)
            # Need to make sure the messages have been flushed to the
            # server.
            session.loop(timeout=0.5)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
