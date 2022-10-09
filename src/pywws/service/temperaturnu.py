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

"""Upload current temperature to temperatur.nu.

temperatur.nu is a Swedish web site that shows the current temperature
in many places.

* Web site: http://www.temperatur.nu/
* Additional dependency: http://docs.python-requests.org/
* Example ``weather.ini`` configuration::

    [temperaturnu]
    hash = longhexnumber

    [live]
    services = ['temperaturnu', 'underground']

    [logged]
    services = ['temperaturnu', 'underground']

You receive the hash value from the temperatur.nu admins during sign
up.  It looks like ``d3b07384d113edec49eaa6238ad5ff00``.

.. _temperatur.nu: http://www.temperatur.nu/

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


class ToService(pywws.service.LiveDataService):
    config = {'hash': ('', True, 'hash')}
    logger = logger
    service_name = service_name
    template = "#live##temp_out \"'t': '%.1f',\"#"

    @contextmanager
    def session(self):
        with requests.Session() as session:
            yield session, 'OK'

    def valid_data(self, data):
        return data['temp_out'] is not None

    def upload_data(self, session, prepared_data={}):
        try:
            rsp = session.get('http://www.temperatur.nu/rapportera.php',
                              params=prepared_data, timeout=60)
        except Exception as ex:
            return False, repr(ex)
        if rsp.status_code != 200:
            return False, 'http status: {:d}'.format(rsp.status_code)
        text = rsp.text.strip()
        if text:
            return True, 'server response "{:s}"'.format(text)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
