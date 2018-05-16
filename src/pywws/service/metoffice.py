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

"""Upload weather data to UK Met Office "WOW".

The UK Met Office runs a `Weather Observations Website`_ (WOW) that
displays readings from amateur and official weather stations. This
module uploads data to it from pywws. You can upload "logged" or "live"
data (or both). The module ensures there is at least 5 minutes between
each reading as required by the API.

* Create account: https://register.metoffice.gov.uk/WaveRegistrationClient/public/newaccount.do?service=weatherobservations
* API: http://wow.metoffice.gov.uk/support/dataformats#automatic
* Example ``weather.ini`` configuration::

    [metoffice]
    site id = 12345678
    aws pin = 987654

    [logged]
    services = ['metoffice', 'underground']

    [live]
    services = ['metoffice', 'underground']

Note that a ``site id`` allocated since June 2016 will probably look
like ``6a571450-df53-e611-9401-0003ff5987fd``.

.. _Weather Observations Website: http://wow.metoffice.gov.uk/home

"""

from __future__ import absolute_import, unicode_literals

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


class ToService(pywws.service.BaseToService):
    catchup = 7
    fixed_data = {'softwaretype': 'pywws-' + pywws.__version__}
    interval = timedelta(seconds=300)
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
"""

    def __init__(self, context):
        # initialise rain history
        last_update = context.status.get_datetime('last update', service_name)
        if last_update:
            last_update = context.calib_data.nearest(last_update)
            self.last_rain = context.calib_data[last_update]['rain']
        else:
            self.last_rain = None
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

    def prepare_data(self, data):
        prepared_data = super(ToService, self).prepare_data(data)
        # compute rain since last upload
        if self.last_rain is not None:
            rain = data['rain'] - self.last_rain
            if rain >= -0.001:
                prepared_data['rainin'] = '{:.4f}'.format(rain_inch(rain))
        self.last_rain = data['rain']
        # compute rain since day start
        day_start = self.context.daily_data.nearest(data['idx'])
        day_start = self.context.daily_data[day_start]['start']
        day_start = self.context.calib_data.after(day_start)
        rain = data['rain'] - self.context.calib_data[day_start]['rain']
        if rain >= -0.001:
            prepared_data['dailyrainin'] = '{:.4f}'.format(rain_inch(rain))
        return prepared_data

    def valid_data(self, data):
        return any([data[x] is not None for x in (
            'wind_dir', 'wind_ave', 'wind_gust', 'hum_out', 'temp_out',
            'rel_pressure')])

    def upload_data(self, session, prepared_data={}, live=False):
        try:
            rsp = session.get('http://wow.metoffice.gov.uk/automaticreading',
                              params=prepared_data, timeout=60)
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
    sys.exit(pywws.service.main(ToService))
