# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2019  pywws contributors

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

"""Upload data to Windy.

`Windy`_  is a Czech company providing interactive
weather forecasting services worldwide.

* Create account: https://stations.windy.com/
* API: `<https://community.windy.com/topic/8168/report-your-weather-station-data-to-windy>`_
* Additional dependency: http://docs.python-requests.org/
* Example ``weather.ini`` configuration::

    [windy]
    api_key = xxxxxxx
    latitude = 43.7
    longitude = 11.7

    [logged]
    services = ['windy', 'underground']

    [live]
    services = ['windy', 'underground']

.. _Windy: http://www.windy.com

"""

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


class ToService(pywws.service.CatchupDataService):
    config = {
        'latitude'    : ('', True, None),
        'longitude'   : ('', True, None),
        'name'        : (None, False, None),
        'station_id'  : ('0', False, 'station'),
        'share_option': (None, False, 'shareOption'),
        'elevation'   : (None, False, None),
        'temp_height' : (None, False, 'tempheight'),
        'wind_height' : (None, False, 'windheight'),
        }

    interval = timedelta(minutes=4)
    logger = logger
    service_name = service_name
    template = """
#live#
#idx          "'ts'          : '%s',"#
#wind_ave     "'wind'        : '%.2f',"#
#wind_dir     "'winddir'     : '%.0f'," "" "winddir_degrees(x)"#
#wind_gust    "'gust'        : '%.2f',"#
#hum_out      "'humidity'    : '%.1f',"#
#temp_out     "'temp'        : '%.2f',"#
#rel_pressure "'mbar'        : '%.2f',"#
#calc "dew_point(data['temp_out'], data['hum_out'])" "'dewpoint': '%.2f',"#
#calc "rain_hour(data)" "'precip': '%.2f',"#
"""

    def __init__(self, context, check_params=True):
        self.API_KEY = context.params.get(self.service_name, 'api_key')
        if not self.API_KEY:
            raise RuntimeError('"api_key" not set in weather.ini')

        super(ToService, self).__init__(context, check_params)

        # extend template
        if context.params.get('config', 'ws type') == '3080':
            self.template += """
#uv           "'uv'            : '%d',"#
"""

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session

    def upload_data(self, session, prepared_data={}):
        url = 'https://stations.windy.com/pws/update/{:s}'.format(self.API_KEY)
        try:
            rsp = session.get(url, params=prepared_data, timeout=60)
        except Exception as ex:
            return False, repr(ex)
        if rsp.status_code != 200:
            return False, 'http status: {:d}'.format(rsp.status_code)
        text = rsp.text.strip()
        lines = text.replace(' ', '\n').replace('\t', '\n').split('\n')
        return 'SUCCESS' in lines, 'server response "{:s}"'.format(text)


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
