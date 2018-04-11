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

from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
from datetime import timedelta
import logging
import os
import sys

import requests

import pywws.service

service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__package__ + '.' + service_name)


class ToService(pywws.service.BaseToService):
    catchup = 7
    fixed_data = {'softwaretype': 'pywws'}
    interval = timedelta(seconds=40)
    logger = logger
    service_name = service_name
    template = """
#live#
#idx          "'datetimeutc': '%Y-%m-%d %H:%M:%S',"#
#temp_out     "'temp'       : '%.1f',"#
#wind_dir     "'wind_dir'   : '%.0f'," "" "winddir_degrees(x)"#
#wind_ave     "'wind_speed' : '%.1f',"#
#wind_gust    "'wind_gust'  : '%.1f',"#
#hum_out      "'humidity'   : '%.d',"#
#rel_pressure "'pressure'   : '%.1f',"#
#calc "rain_hour(data)" "'rain_1h': '%.1f',"#
#calc "rain_day(data)" "'rain_today': '%.1f',"#
#calc "dew_point(data['temp_out'], data['hum_out'])" "'dewpoint': '%.1f',"#
"""

    def __init__(self, context):
        # extend template
        if context.params.get('config', 'ws type') == '3080':
            self.template += """
#illuminance  "'lum': '%.2f'," "" "illuminance_wm2(x)"#
#uv           "'uv' : '%d',"#
"""
        # set up authorisation
        self.params = {
            'user'    : context.params.get(service_name, 'user', 'unknown'),
            'password': context.params.get(service_name, 'password', 'unknown'),
            }
        # get configurable "fixed data"
        self.fixed_data.update({
            'name': context.params.get(service_name, 'id', 'unknown'),
            'lat' : context.params.get(service_name, 'lat', 'unknown'),
            'long': context.params.get(service_name, 'long', 'unknown'),
            'alt' : context.params.get(service_name, 'alt', 'unknown'),
            })
        # base class init
        super(ToService, self).__init__(context)

    @contextmanager
    def session(self):
        with requests.Session() as session:
            session.auth = self.params['user'], self.params['password']
            yield session

    def valid_data(self, data):
        return True

    def upload_data(self, session, prepared_data, live):
        try:
            rsp = session.post('http://openweathermap.org/data/post',
                               data=prepared_data, timeout=30)
        except Exception as ex:
            return False, str(ex)
        if rsp.status_code != 200:
            return False, 'http status: {:d}'.format(rsp.status_code)
        rsp = rsp.json()
        if rsp:
            return True, 'server response "{!r}"'.format(rsp)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService, 'Upload data to OpenWeatherMap'))
