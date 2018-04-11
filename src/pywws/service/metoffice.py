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

import pywws
import pywws.service

service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__package__ + '.' + service_name)


class ToService(pywws.service.BaseToService):
    catchup = 7
    fixed_data = {'softwaretype': 'pywws v' + pywws.__version__}
    interval = timedelta(seconds=290)
    logger = logger
    service_name = service_name
    template = """
#live#
#idx          "'dateutc'    : '%Y-%m-%d %H:%M:%S',"#
#wind_dir     "'winddir'    : '%.0f'," "" "winddir_degrees(x)"#
#wind_ave     "'windspeedms': '%.1f',"#
#wind_gust    "'windgustms' : '%.f',"#
#hum_out      "'humidity'   : '%.d',"#
#temp_out     "'tempc'      : '%.1f',"#
#rel_pressure "'mslphpa'    : '%.1f',"#
#calc "dew_point(data['temp_out'], data['hum_out'])" "'dewptc': '%.1f',"#
#calc "rain_hour(data)" "'rainmm': '%g',"#
#calc "rain_day(data)" "'dailyrainmm': '%g',"#
"""

    def __init__(self, context):
        # get configurable "fixed data"
        self.fixed_data.update({
            'siteid'               : context.params.get(
                service_name, 'site id', 'unknown'),
            'siteAuthenticationKey': context.params.get(
                service_name, 'aws pin', 'unknown'),
            })
        # base class init
        super(ToService, self).__init__(context)

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session

    def valid_data(self, data):
        return any([data[x] is not None for x in (
            'wind_dir', 'wind_ave', 'wind_gust', 'hum_out', 'temp_out',
            'rel_pressure')])

    def upload_data(self, session, prepared_data, live):
        try:
            rsp = session.get('http://wow.metoffice.gov.uk/automaticreading',
                              params=prepared_data, timeout=30)
        except Exception as ex:
            return False, str(ex)
        if rsp.status_code == 429:
            # UK Met Office server uses 429 to signal duplicate data
            return True, 'repeated data {:s}'.format(prepared_data['dateutc'])
        if rsp.status_code != 200:
            return False, 'http status: {:d}'.format(rsp.status_code)
        rsp = rsp.json()
        if rsp:
            return True, 'server response "{!r}"'.format(rsp)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService, 'Upload data to UK Met Office'))
