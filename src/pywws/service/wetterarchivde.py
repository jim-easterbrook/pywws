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

"""Upload weather data to wetter.com.

wetter.com_ is a web site gathering data mainly from stations in
Germany. It's referred to in pywws as wetterarchivde for historical
reasons.

* Register station: https://www.wetter.com/mein_wetter/login/
* Additional dependency: http://docs.python-requests.org/
* Example ``weather.ini`` configuration::

    [wetterarchivde]
    user_id = 12345
    kennwort = ab1d3456i8

    [logged]
    services = ['wetterarchivde', 'underground']

    [live]
    services = ['wetterarchivde', 'underground']

.. _wetter.com: http://netzwerk.wetter.com/

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


class ToService(pywws.service.CatchupDataService):
    config = {
        'user_id' : ('', True, 'id'),
        'kennwort': ('', True, 'pwd'),
        }
    fixed_data = {'sid': 'pywws'}
    interval = timedelta(seconds=300)
    logger = logger
    service_name = service_name
    template = """
#live#
#roundtime True#
#idx                    "'dtutc': '%Y%m%d%H%M',"#
#timezone local#
#idx                    "'dt': '%Y%m%d%H%M',"#
#hum_out                "'hu': '%.d',"#
#temp_out               "'te': '%.1f',"#
#rel_pressure           "'pr': '%.1f',"#
#wind_dir               "'wd': '%.0f'," "" "winddir_degrees(x)"#
#wind_ave               "'ws': '%.1f',"#
#wind_gust              "'wg': '%.1f',"#
#calc "rain_hour(data)" "'pa': '%.1f',"#
"""

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        # extend template
        if context.params.get('config', 'ws type') == '3080':
            self.template += """#uv "'uv': '%d',"#"""

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session, 'OK'

    def upload_data(self, session, prepared_data={}):
        try:
            rsp = session.post('http://interface.wetterarchiv.de/weather/',
                               data=prepared_data, timeout=60)
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
