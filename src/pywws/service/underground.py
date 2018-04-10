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


class WUUploader(pywws.service.BaseUploader):
    logger = logger
    service_name = service_name

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session

    def upload(self, session, prepared_data, live):
        if live:
            prepared_data.update({'realtime': '1', 'rtfreq': '48'})
            url = 'https://rtupdate.wunderground.com/'
        else:
            url = 'https://weatherstation.wunderground.com/'
        url += 'weatherstation/updateweatherstation.php'
        try:
            rsp = session.get(url, params=prepared_data, timeout=30)
        except Exception as ex:
            return False, str(ex)
        if rsp.status_code != 200:
            return False, 'http status: {:d}'.format(rsp.status_code)
        text = rsp.text.strip()
        return text == 'success', 'server response "{:s}"'.format(text)


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
        if eval(context.params.get(service_name, 'internal', 'False')):
            self.template += """
#hum_in       "'indoorhumidity': '%.d',"#
#temp_in      "'indoortempf'   : '%.1f'," "" "temp_f(x)"#
"""
        # get configurable "fixed data"
        self.fixed_data.update({
            'ID'      : context.params.get(service_name, 'station', 'unknown'),
            'PASSWORD': context.params.get(service_name, 'password', 'unknown'),
            })
        # base class init
        super(ToService, self).__init__(context, WUUploader(context))


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService, 'Upload data to Weather Underground'))
