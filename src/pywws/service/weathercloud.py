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

"""Upload data to WeatherCloud.

* Create account: https://weathercloud.net/
* Additional dependency: http://docs.python-requests.org/
* Example ``weather.ini`` configuration::

    [weathercloud]
    deviceid = XXXXXXXXXXXX
    devicekey = XXXXXXXXXXXXXXXXXXXXXXXXXXXXX

    [logged]
    services = ['weathercloud', 'metoffice']

.. _WeatherCloud: http://www.weathercloud.net/

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


class ToService(pywws.service.LiveDataService):
    config = {
        'deviceid' : ('', True, 'wid'),
        'devicekey': ('', True, 'key'),
        }
    fixed_data = {'ver': pywws.__version__, 'type': '481'}
    interval = timedelta(seconds=600)
    logger = logger
    service_name = service_name
    template = """
#live#
#temp_in                                                    "'tempin'   : '%.1f',"#
#temp_out                                                   "'temp'     : '%.1f',"#
#calc "wind_chill(data['temp_out'], data['wind_ave'])"      "'chill'    : '%.1f',"#
#calc "dew_point(data['temp_in'], data['hum_in'])"          "'dewin'    : '%.1f',"#
#calc "dew_point(data['temp_out'], data['hum_out'])"        "'dew'      : '%.1f',"#
#calc "usaheatindex(data['temp_in'], data['hum_in'], dew_point(data['temp_in'], data['hum_in']))" "'heatin' : '%.1f',"#
#calc "usaheatindex(data['temp_out'], data['hum_out'], dew_point(data['temp_out'], data['hum_out']))" "'heat' : '%.1f',"#
#calc "(usaheatindex(data['temp_out'], data['hum_out'], dew_point(data['temp_out'], data['hum_out'])) - (1.072 * wind_mph(data['wind_ave']))) " "'thw' : '%.1f',"#
#hum_in                                                     "'humin'    : '%.d',"#
#hum_out                                                    "'hum'      : '%.d',"#
#wind_ave                                                   "'wspdavg'  : '%.1f',"#
#wind_gust                                                  "'wspdhi'   : '%.1f',"#
#wind_dir                                                   "'wdiravg'  : '%.1f'," "" "winddir_degrees(x)"#
#rel_pressure                                               "'bar'      : '%.1f',"#
#calc "rain_day(data)"                                      "'rain'     : '%.1f',"#
#calc "rain_hour(data)"                                     "'rainrate' : '%.1f',"#
#idx                                                        "'time'     : '%Y%m%d %H%M%S',"#
"""

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        # extend template
        if context.params.get('config', 'ws type') == '3080':
            self.template += """
#calc "data['illuminance']"                                 "'solarrad' : '%.1f'," "" "illuminance_wm2(x)"#
#calc "data['uv']"                                          "'uvi'      : '%.1f',"#
"""

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session
	
    def valid_data(self, data):
        return any([data[x] is not None for x in (
            'wind_dir', 'wind_ave', 'wind_gust', 'hum_out', 'temp_out',
            'temp_in', 'hum_in', 'rel_pressure')])
	
    def upload_data(self, session, prepared_data={}, live=False):
        
        url = 'http://api.weathercloud.net/v01/set'
        for key in ('tempin', 'temp', 'chill', 'dewin', 'dew', 
                    'heatin', 'heat', 'thw', 'wspdavg', 'wspdhi', 
                    'bar', 'rain', 'rainrate', 'solarrad', 'uvi'): 
            if key in prepared_data: 
                prepared_data[key] = prepared_data[key].replace('.', '')
        try:
            rsp = session.get(url, params=prepared_data, timeout=60)
        except Exception as ex:
            return False, str(ex)
        text = rsp.text.strip()
        if rsp.text.strip() == '400':
            # WeatherCloud server uses 400 to signal bad request
            return False, 'bad request: "{:s}"'.format(rsp.text.strip())
        if rsp.text.strip() == '401':
            # WeatherCloud server uses 401 to signal invalid wid or key
            return False, 'invalid wid or key: "{:s}"'.format(rsp.text.strip())
        if rsp.text.strip() == '429':
            # WeatherCloud server uses 429 to signal too frequent data upload
            return False, 'too frequent data: "{:s}"'.format(rsp.text.strip())
        if rsp.text.strip() != '200':
            return False, 'unknown error: "{:s}"'.format(rsp.text.strip())
        if rsp.text.strip() == '200':
            return True, 'upload successful: "{:s}"'.format(rsp.text.strip())
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
