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

"""Upload weather data to an AWS Gateway API (or other) service.

This is for any service that accepts key value data via a GET method. This
supports optional extra headers.

* Additional dependency: http://docs.python-requests.org/
* Example ``weather.ini`` configuration::

    [aws_api_gw_service]
    api url	= https://my-aws-api-gw.execute-api.eu-west-1.amazonaws.com/weather
    http headers	= [('x-api-key', 'my-api-key'), ('another-one', 'spam-val')]

    [logged]
    services = ['aws_api_gw_service', 'metoffice']

    [live]
    services = ['aws_api_gw_service', 'metoffice']

"""

from __future__ import absolute_import, unicode_literals

from ast import literal_eval
from contextlib import contextmanager
from datetime import timedelta
import logging
import os
import sys

import requests

import pywws
from pywws.conversions import rain_inch
import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.CatchupDataService):
    catchup = 100
    config = {
        'http headers': (None, False, None),
        'api url'     : ('',   True,  None),
        }
    interval = timedelta(seconds=300)
    logger = logger
    service_name = service_name
    template = """
#live#
#hum_in       "'hum_in'     : '%.d',"#
#temp_in      "'temp_in'    : '%.1f',"#
#hum_out      "'hum_out'    : '%.d',"#
#temp_out     "'temp_out'   : '%.1f',"#
#calc "dew_point(data['temp_out'], data['hum_out'])" "'temp_dewpt'  : '%.1f',"#
#rel_pressure "'abs_pressure'   : '%.4f',"#
#wind_ave     "'wind_ave'   : '%.2f'," "" "wind_mph(x)"#
#wind_gust    "'wind_gust'  : '%.2f'," "" "wind_mph(x)"#
#wind_dir     "'wind_dir'   : '%.0f'," "" "winddir_degrees(x)"#
#calc "rain_hour(data)" "'rain'     : '%g',"#
#calc "rain_day(data)" "'rain_day'     : '%g',"#
#calc "wind_chill(data['temp_out'], data['wind_ave'])" "'wind_chill'	: '%.1f',"#
#calc "apparent_temp(data['temp_out'], data['hum_out'], data['wind_ave'])" "'temp_apprt'	:  '%.1f',"#
#calc "cloud_base(data['temp_out'], data['hum_out'])" "'cloud_base' : '%.1f',"#
#idx          "'tdate'      : '%Y-%m-%d',"#
#idx          "'ttime'      : '%H:%M:%S',"#

"""

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        # initialise rain history
        last_update = context.status.get_datetime('last update', service_name)
        if last_update:
            last_update = context.calib_data.nearest(last_update)
            self.last_rain = context.calib_data[last_update]['rain']
        else:
            self.last_rain = None

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session

    def upload_data(self, session, prepared_data={}):
        try:
            if self.params['http headers']:
                for header in literal_eval(self.params['http headers']):
                    session.headers.update({header[0]: header[1]})
            rsp = session.get(self.params['api url'], params=prepared_data,
                timeout=60)
        except Exception as ex:
            return False, repr(ex)
        if rsp.status_code != 200:
            return False, 'http status: {:d}'.format(rsp.status_code)
        rsp = rsp.json()
        if rsp:
            return True, 'server response "{!r}"'.format(rsp)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
