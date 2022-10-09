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

"""Upload weather data to Open Weather Map.

`Open Weather Map`_ is a Latvian based IT company seeking to provide
affordable weather data.

* Create account: https://home.openweathermap.org/users/sign_up
* API: https://openweathermap.org/stations
* Additional dependency: http://docs.python-requests.org/
* Example ``weather.ini`` configuration::

    [openweathermap]
    api key = b1b15e88fa797225412429c1c50c122a1
    external id = SW1Aweather
    station name = Buck House
    lat = 51.501
    long = -0.142
    alt = 10
    station id = 583436dd9643a9000196b8d6

    [logged]
    services = ['openweathermap', 'underground']

Configuring pywws to use Open Weather Map is a bit more complicated than
with other services. Start by running the module to set some default
values in weather.ini (with no other pywws software running)::

    python -m pywws.service.openweathermap data_dir

After signing up and logging in to Open Weather Map visit the `API keys
page`_ and copy your default key to the ``api key`` entry in
weather.ini. The ``external id`` field is a single word name to identify
your station. You could use a name based on your post code, or maybe
your id from Weather Underground or CWOP. The ``station name`` is a
longer, human readable, name. I'm not sure what use Open Weather Map
makes of either of these. ``lat`` and ``long`` should be set to the
latitude and longitude of your station (in degrees) and ``alt`` to its
altitude in metres.

After setting (or changing) the above fields you need to "register" your
station with Open Weather Map. This is done by running the module with
the ``-r`` flag::

    python -m pywws.service.openweathermap -r -v data_dir

If you already have any stations registered with Open Weather Map this
will show you their details. You can select one of these existing
stations or register a new one. pywws then sends the configuration
values from weather.ini to Open Weather Map.

If this succeeds then Open Weather Map will have allocated a ``station
id`` value which pywws stores in weather.ini. All this complication is
to allow more than one station to be attached to one user's account.

.. _Open Weather Map: https://openweathermap.org/
.. _API keys page: https://home.openweathermap.org/api_keys

"""

from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
from datetime import timedelta
import json
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
        'api key'     : ('', True,  None),
        'station id'  : ('', True,  'station_id'),
        'external id' : ('', False, None),
        'station name': ('', False, None),
        'lat'         : ('', False, None),
        'long'        : ('', False, None),
        'alt'         : ('', False, None),
        }
    logger = logger
    service_name = service_name
    template = """
#live#
#idx          "'dt'         : %s,"#
#temp_out     "'temperature': %.1f,"#
#wind_ave     "'wind_speed' : %.1f,"#
#wind_gust    "'wind_gust'  : %.1f,"#
#wind_dir     "'wind_deg'   : %.0f," "" "winddir_degrees(x)"#
#rel_pressure "'pressure'   : %.1f,"#
#hum_out      "'humidity'   : %.d,"#
#calc "rain_hour(data)" "'rain_1h': %.1f,"#
#calc "rain_24hr(data)" "'rain_24h': %.1f,"#
#calc "dew_point(data['temp_out'], data['hum_out'])" "'dew_point': %.1f,"#
"""

    @contextmanager
    def session(self):
        with requests.Session() as session:
            session.headers.update({'Content-Type': 'application/json'})
            session.params.update({'appid': self.params['api key']})
            yield session, 'OK'

    def upload_data(self, session, prepared_data={}):
        url = 'https://api.openweathermap.org/data/3.0/measurements'
        try:
            rsp = session.post(url, json=[prepared_data], timeout=60)
        except Exception as ex:
            return False, repr(ex)
        if rsp.status_code != 204:
            return False, 'http status: {:d} {:s}'.format(
                rsp.status_code, rsp.text)
        return True, 'OK'

    def register(self):
        import pprint

        self.check_params('external id', 'station name', 'lat', 'long', 'alt')
        url = 'https://api.openweathermap.org/data/3.0/stations'
        data = {
            'external_id': self.params['external id'],
            'name'       : self.params['station name'],
            'latitude'   : float(self.params['lat']),
            'longitude'  : float(self.params['long']),
            'altitude'   : float(self.params['alt']),
            }
        station_id = self.params['station id']
        idx = -1
        with self.session() as session:
            # get current stations
            try:
                rsp = session.get(url, timeout=60)
            except Exception as ex:
                print('exception', repr(ex))
                return
            stations = rsp.json()
            if stations:
                print('The following stations are registered to your account')
                for i, station in enumerate(stations):
                    if station['id'] == station_id:
                        idx = i
                        print('Number:', i, '\t\t\t\t<- current station')
                    else:
                        print('Number:', i)
                    pprint.pprint(station)
                if sys.version_info[0] >= 3:
                    input_ = input
                else:
                    input_ = raw_input
                i = input_('Please enter number of station to use, or N' +
                           ' to register a new station: ')
                if i in ('N', 'n'):
                    idx = -1
                    station_id = None
                else:
                    idx = int(i)
                    station_id = stations[idx]['id']
                for i, station in enumerate(stations):
                    if i == idx:
                        continue
                    yn = input_('Would you like to delete station number' +
                                ' {} and all its data (Y/N)? '.format(i))
                    if yn in ('Y', 'y'):
                        try:
                            session.delete(
                                url + '/' + station['id'], timeout=60)
                        except Exception as ex:
                            print('exception', repr(ex))
                            return
            if station_id:
                # update existing station
                logger.debug('Udating station id ' + station_id)
                url += '/' + station_id
                try:
                    rsp = session.put(url, json=data, timeout=60)
                except Exception as ex:
                    print('exception', repr(ex))
                    return
                rsp = rsp.json()
                logger.debug('response: ' + repr(rsp))
            else:
                # create new station
                logger.debug('Creating new station')
                try:
                    rsp = session.post(url, json=data, timeout=60)
                except Exception as ex:
                    print('exception', repr(ex))
                    return
                rsp = rsp.json()
                logger.debug('response: ' + repr(rsp))
            for key in 'id', 'ID':
                if key in rsp:
                    self.context.params.set(
                        service_name, 'station id', rsp[key])


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
