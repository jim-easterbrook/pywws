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

from __future__ import absolute_import, print_function, unicode_literals

from contextlib import contextmanager
from datetime import timedelta
import logging
import os
import socket
import sys

import pywws
import pywws.service

service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__package__ + '.' + service_name)


class APRSUploader(pywws.service.BaseUploader):
    logger = logger
    service_name = service_name

    @contextmanager
    def session(self):
        yield None

    def upload(self, session, prepared_data, live):
        if prepared_data['passcode'] == '-1':
            server = 'cwop.aprs.net', 14580
        else:
            server = 'rotate.aprs.net', 14580
        login = ('user {designator:s} pass {passcode:s} ' +
                 'vers pywws {version:s}\n').format(**prepared_data)
        logger.debug('login: "{:s}"'.format(login))
        login = login.encode('ASCII')
        packet = ('{designator:s}>APRS,TCPIP*:@{idx:s}' +
                  'z{latitude:s}/{longitude:s}' +
                  '_{wind_dir:s}/{wind_ave:s}g{wind_gust:s}t{temp_out:s}' +
                  'r{rain_hour:s}P{rain_day:s}b{rel_pressure:s}h{hum_out:s}' +
                  '.pywws-{version:s}\n').format(**prepared_data)
        logger.debug('packet: "{:s}"'.format(packet))
        packet = packet.encode('ASCII')
        sock = socket.socket()
        sock.settimeout(20)
        try:
            sock.connect(server)
            try:
                response = sock.recv(4096)
                logger.debug('server software: %s', response.strip())
                sock.sendall(login)
                response = sock.recv(4096)
                logger.debug('server login ack: %s', response.strip())
                sock.sendall(packet)
                sock.shutdown(socket.SHUT_RDWR)
            finally:
                sock.close()
        except Exception as ex:
            return(str(ex))
        return ''


class ToService(pywws.service.BaseToService):
    catchup = 0
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
'rain_day'     : #calc "100.0*rain_inch(rain_day(data))"  "'%03.0f'," "'...',"#
"""

    def __init__(self, context):
        # get configurable "fixed data"
        self.fixed_data.update({
            'designator': context.params.get(
                service_name, 'designator', 'unknown'),
            'passcode': context.params.get(
                service_name, 'passcode', '-1'),
            'latitude': context.params.get(
                service_name, 'latitude', 'unknown'),
            'longitude': context.params.get(
                service_name, 'longitude', 'unknown'),
            })
        # base class init
        super(ToService, self).__init__(context, APRSUploader(context))


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService, 'Upload data to CWOP'))
