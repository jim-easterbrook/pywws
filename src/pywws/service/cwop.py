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

"""Upload weather data to Citizen Weather Observer Program.

The `Citizen Weather Observer Program`_ (CWOP) is a north American
public-private partnership to gather weather data. This module uploads
data to it from pywws. You can upload "logged" or "live" data (or both).
The module ensures there is at least 5 minutes between each reading as
required by the API.

* Create account: http://www.wxqa.com/SIGN-UP.html
* API: http://www.wxqa.com/faq.html
* Example ``weather.ini`` configuration::

    [cwop]
    designator = EW9999
    latitude = 5130.06N
    longitude = 00008.52E
    passcode = -1

    [logged]
    services = ['cwop', 'underground']

    [live]
    services = ['cwop', 'underground']

Note that the latitude and longitude must be in "LORAN" format and
leading zeros are required. See question 3 in the `CWOP FAQ`_ for more
information.

Licensed radio hams use their callsign as the designator and need a
passcode. Other users should leave the passcode at its default value of
``-1``.

The CWOP/APRS uploader is based on code by Marco Trevisan <mail@3v1n0.net>.

.. _Citizen Weather Observer Program: http://www.wxqa.com/
.. _CWOP FAQ: http://www.wxqa.com/faq.html

"""

from __future__ import absolute_import, print_function, unicode_literals

from contextlib import closing, contextmanager
from datetime import timedelta
import logging
import os
import socket
import sys

import pywws
import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.LiveDataService):
    config = {
        'designator': ('',   True, 'designator'),
        'passcode'  : ('-1', True, 'passcode'),
        'latitude'  : ('',   True, 'latitude'),
        'longitude' : ('',   True, 'longitude'),
        }
    fixed_data = {'version': pywws.__version__}
    interval = timedelta(seconds=290)
    logger = logger
    service_name = service_name
    template = """
#live#
'idx'          : #idx          "'%d%H%M',"#
'wind_dir'     : #wind_dir     "'%03.0f'," "'...',"   "winddir_degrees(x)"#
'wind_ave'     : #wind_ave     "'%03.0f'," "'...',"   "wind_mph(x)"#
'wind_gust'    : #wind_gust    "'%03.0f'," "'...',"   "wind_mph(x)"#
'temp_out'     : #temp_out     "'%03.0f'," "'...',"   "temp_f(x)"#
'hum_out'      : #hum_out      "'%02d',"   "'..',"    "x % 100"#
'rel_pressure' : #rel_pressure "'%05.0f'," "'.....'," "x * 10.0"#
'rain_hour'    : #calc "100.0*rain_inch(rain_hour(data))" "'%03.0f'," "'...',"#
'rain_24hr'    : #calc "100.0*rain_inch(rain_24hr(data))" "'%03.0f'," "'...',"#
"""

    @contextmanager
    def session(self):
        with closing(socket.socket()) as session:
            session.settimeout(20)
            server = ('rotate.aprs.net',
                      'cwop.aprs.net')[self.fixed_data['passcode'] == '-1']
            session.connect((server, 14580))
            response = session.recv(4096).decode('ASCII')
            logger.debug('server software: %s', response.strip())
            yield session

    def upload_data(self, session, prepared_data={}):
        login = ('user {designator:s} pass {passcode:s} ' +
                 'vers pywws {version:s}\n').format(**prepared_data)
        logger.debug('login: "{:s}"'.format(login))
        login = login.encode('ASCII')
        packet = ('{designator:s}>APRS,TCPIP*:@{idx:s}' +
                  'z{latitude:s}/{longitude:s}' +
                  '_{wind_dir:s}/{wind_ave:s}g{wind_gust:s}t{temp_out:s}' +
                  'r{rain_hour:s}p{rain_24hr:s}b{rel_pressure:s}h{hum_out:s}' +
                  '.pywws-{version:s}\n').format(**prepared_data)
        logger.debug('packet: "{:s}"'.format(packet))
        packet = packet.encode('ASCII')
        try:
            session.sendall(login)
            response = session.recv(4096).decode('ASCII')
            logger.debug('server login ack: %s', response.strip())
            session.sendall(packet)
            session.shutdown(socket.SHUT_RDWR)
        except Exception as ex:
            return False, repr(ex)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
