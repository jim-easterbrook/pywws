# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2018-19  pywws contributors

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
    internal = True

    [logged]
    services = ['weathercloud', 'metoffice']

.. _WeatherCloud: http://www.weathercloud.net/

"""

from __future__ import absolute_import, unicode_literals

from ast import literal_eval
from contextlib import contextmanager
from datetime import timedelta
import logging
import os
import sys
if sys.version_info[0] < 3:
    from httplib import responses
else:
    from http.client import responses

import requests

from pywws.conversions import usaheatindex, wind_mph
import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.LiveDataService):
    config = {
        'deviceid' : ('',      True, 'wid'),
        'devicekey': ('',      True, 'key'),
        'internal' : ('False', True, None),
        }
    fixed_data = {'ver': pywws.__version__, 'type': '481'}
    interval = timedelta(seconds=600)
    logger = logger
    service_name = service_name
    template = """
#live#
#temp_out
    "'temp'     : '%.0f'," "" "scale(x, 10.0)"#
#calc "wind_chill(data['temp_out'], data['wind_ave'])"
    "'chill'    : '%.0f'," "" "scale(x, 10.0)"#
#calc "dew_point(data['temp_out'], data['hum_out'])"
    "'dew'      : '%.0f'," "" "scale(x, 10.0)"#
#calc "usaheatindex(data['temp_out'], data['hum_out'])"
    "'heat'     : '%.0f'," "" "scale(x, 10.0)"#
#hum_out
    "'hum'      : '%.d',"#
#wind_ave
    "'wspdavg'  : '%.0f'," "" "scale(x, 10.0)"#
#wind_ave
    "'wspd'     : '%.0f'," "" "scale(x, 10.0)"#
#wind_gust
    "'wspdhi'   : '%.0f'," "" "scale(x, 10.0)"#
#wind_dir
    "'wdiravg'  : '%.0f'," "" "winddir_degrees(x)"#
#wind_dir
    "'wdir'     : '%.0f'," "" "winddir_degrees(x)"#
#rel_pressure
    "'bar'      : '%.0f'," "" "scale(x, 10.0)"#
#calc "rain_day(data)"
    "'rain'     : '%.0f'," "" "scale(x, 10.0)"#
#calc "rain_hour(data)"
    "'rainrate' : '%.0f'," "" "scale(x, 10.0)"#
#idx
    "'time'     : '%Y%m%d %H%M%S',"#
"""

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        # extend template
        if context.params.get('config', 'ws type') == '3080':
            self.template += """
#illuminance
    "'solarrad': '%.0f'," "" "scale(illuminance_wm2(x), 10.0)"#
#uv
    "'uvi'     : '%.0f'," "" "scale(x, 10.0)"#
"""
        if literal_eval(self.params['internal']):
            self.template += """
#temp_in
    "'tempin'  : '%.0f'," "" "scale(x, 10.0)"#
#hum_in
    "'humin'   : '%.d',"#
#calc "dew_point(data['temp_in'], data['hum_in'])"
    "'dewin'   : '%.0f'," "" "scale(x, 10.0)"#
#calc "usaheatindex(data['temp_in'], data['hum_in'])"
    "'heatin'  : '%.0f'," "" "scale(x, 10.0)"#
"""

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session

    def valid_data(self, data):
        return any([data[x] is not None for x in (
            'wind_dir', 'wind_ave', 'wind_gust', 'hum_out', 'temp_out',
            'temp_in', 'hum_in', 'rel_pressure')])

    def upload_data(self, session, prepared_data={}):
        url = 'http://api.weathercloud.net/v01/set'
        try:
            rsp = session.get(url, params=prepared_data, timeout=60)
        except Exception as ex:
            return False, repr(ex)
        text = rsp.text.strip()
        if text == '200':
            return True, 'OK'
        if text in responses:
            return False, '{} ({})'.format(responses[text], text)
        return False, 'unknown error ({})'.format(text)


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
