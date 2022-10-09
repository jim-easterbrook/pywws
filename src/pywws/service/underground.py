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

"""Upload data to Weather Underground.

`Weather Underground`_ may be the oldest and best known site gathering
data from amateur weather stations.

* Create account: https://www.wunderground.com/signup
* API: `<https://support.weather.com/s/article/PWS-Upload-Protocol>`_
* Additional dependency: http://docs.python-requests.org/
* Example ``weather.ini`` configuration::

    [underground]
    station = ABCDEFGH1
    password = xxxxxxx
    internal = False

    [logged]
    services = ['underground', 'metoffice']

    [live]
    services = ['underground', 'metoffice']

The ``internal`` configuration setting allows you to include indoor
temperature and humidity in your uploads.

Note that ``password`` is not the password you use to log in to Weather
Underground, it's the ``Key`` value shown on your list of devices:
https://www.wunderground.com/member/devices

Previous versions of pywws had an extra ``underground_rf`` service to
use Weather Underground's "rapid fire" server for frequent uploads. Now
the rapid fire server is used automatically for "live" data and the
normal server for past data.

.. _Weather Underground: http://www.wunderground.com/

"""

from __future__ import absolute_import, unicode_literals

from ast import literal_eval
from contextlib import contextmanager
from datetime import datetime, timedelta
import logging
import os
import sys

import requests

import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)
RTFREQ = timedelta(seconds=48)


class ToService(pywws.service.CatchupDataService):
    config = {
        'station' : ('',      True, 'ID'),
        'password': ('',      True, 'PASSWORD'),
        'internal': ('False', True, None),
        }
    fixed_data = {'action': 'updateraw', 'softwaretype': 'pywws'}
    interval = timedelta(seconds=47)
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

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        # extend template
        if context.params.get('config', 'ws type') == '3080':
            self.template += """
#illuminance  "'solarradiation': '%.2f'," "" "illuminance_wm2(x)"#
#uv           "'UV'            : '%d',"#
"""
        if literal_eval(self.params['internal']):
            self.template += """
#hum_in       "'indoorhumidity': '%.d',"#
#temp_in      "'indoortempf'   : '%.1f'," "" "temp_f(x)"#
"""

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session, 'OK'

    def upload_data(self, session, prepared_data={}):
        # extract timestamp from prepared_data
        idx = datetime.strptime(prepared_data['dateutc'], '%Y-%m-%d %H:%M:%S')
        # use "rapid fire" server if data is current
        if datetime.utcnow() - idx < RTFREQ:
            prepared_data.update({'realtime': '1', 'rtfreq': '48'})
            url = 'https://rtupdate.wunderground.com/'
        else:
            url = 'https://weatherstation.wunderground.com/'
        url += 'weatherstation/updateweatherstation.php'
        try:
            rsp = session.get(url, params=prepared_data, timeout=60)
        except Exception as ex:
            return False, repr(ex)
        if rsp.status_code != 200:
            return False, 'http status: {:d}'.format(rsp.status_code)
        text = rsp.text.strip()
        return text == 'success', 'server response "{:s}"'.format(text)


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
