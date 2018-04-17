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

"""Upload weather data to PWS Weather.

`PWS Weather`_ is a site run by AerisWeather_ that "brings together
personal weather station data worldwide from locales not served by
primary weather services."

* Create account: http://www.pwsweather.com/register.php
* API based on WU protocol: `<http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol>`_
* Example ``weather.ini`` configuration::

    [pwsweather]
    station = ABCDEFGH1
    password = xxxxxxx

    [logged]
    services = ['pwsweather', 'underground']

.. _PWS Weather: http://www.pwsweather.com/
.. _AerisWeather: https://www.aerisweather.com/

"""

from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
from datetime import timedelta
import logging
import os
import sys

import requests

import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.BaseToService):
    catchup = 7
    fixed_data = {'action': 'updateraw', 'softwaretype': 'pywws'}
    interval = timedelta(seconds=40)
    logger = logger
    service_name = service_name
    template = """
#live#
#idx          "'dateutc'     : '%Y-%m-%d %H:%M:%S',"#
#wind_dir     "'winddir'     : '%.0f'," "" "winddir_degrees(x)"#
#wind_ave     "'windspeedmph': '%.2f'," "" "wind_mph(x)"#
#wind_gust    "'windgustmph' : '%.2f'," "" "wind_mph(x)"#
#hum_out      "'humidity'    : '%.d',"#
#temp_out     "'tempf'       : '%.1f'," "" "temp_f(x)"#
#rel_pressure "'baromin'     : '%.4f'," "" "pressure_inhg(x)"#
#calc "temp_f(dew_point(data['temp_out'], data['hum_out']))" "'dewptf': '%.1f',"#
#calc "rain_inch(rain_hour(data))" "'rainin': '%g',"#
#calc "rain_inch(rain_day(data))" "'dailyrainin': '%g',"#
"""

    def __init__(self, context):
        # extend template
        if context.params.get('config', 'ws type') == '3080':
            self.template += """
#illuminance  "'solarradiation': '%.2f'," "" "illuminance_wm2(x)"#
#uv           "'UV'            : '%d',"#
"""
        # get configurable "fixed data"
        self.fixed_data.update({
            'ID'      : context.params.get(service_name, 'station', 'unknown'),
            'PASSWORD': context.params.get(service_name, 'password', 'unknown'),
            })
        # base class init
        super(ToService, self).__init__(context)

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session

    def upload_data(self, session, prepared_data={}, live=False):
        try:
            rsp = session.get(
                'http://www.pwsweather.com/pwsupdate/pwsupdate.php',
                params=prepared_data, timeout=60)
        except Exception as ex:
            return False, str(ex)
        if rsp.status_code != 200:
            return False, 'http status: {:d}'.format(rsp.status_code)
        text = rsp.text.strip()
        if text:
            return True, 'server response "{:s}"'.format(text)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService, 'Upload data to PWSWeather'))
