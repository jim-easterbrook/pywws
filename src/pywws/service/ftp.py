# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-18  pywws contributors

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

"""Upload files to a web server by FTP.

This module uploads files to (typically) a website *via* FTP. Details of
the upload destination are stored in the file ``weather.ini`` in your
data directory. You should be able to get the required information from
your web space provider. If your provider allows SFTP then you could use
:py:mod:`pywws.service.sftp` for greater security.

* Example ``weather.ini`` configuration::

    [ftp]
    site = ftp.xxxx.yyyy.co.uk
    user = xxxxxxx
    password = zzzzzzzzz
    directory = public_html/weather/data/
    port = 21

    [hourly]
    plot = ['24hrs.png.xml', 'rose_12hrs.png.xml']
    text = ['24hrs.txt']
    services = [('ftp', '24hrs.txt', '24hrs.png', 'rose_12hrs.png')]

Run :py:mod:`pywws.service.ftp` once to set the default configuration,
which you can then change. ``directory`` is the name of a directory in
which all the uploaded files will be put. This will depend on the
structure of your web site and the sort of host you use. ``port`` is the
port number to use. 21 is the standard value but your web space provider
may require a different port.

You can upload any files you like, as often as you like, but typical
usage is to update a website once an hour. Each file to be uploaded
needs to be listed in a service entry like ``('ftp', 'filename')``. If
the file is not in your ``work`` directory's ``output`` directory then
``filename`` should be the full path.

"""

from __future__ import absolute_import

from contextlib import closing, contextmanager
from datetime import timedelta
import ftplib
import logging
import os
import sys

import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.FileService):
    config = {
        'site'       : ('',   True, None),
        'user'       : ('',   True, None),
        'password'   : ('',   True, None),
        'directory'  : ('',   True, None),
        'port'       : ('21', True, None),
        }
    logger = logger
    service_name = service_name

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        self.params['port'] = int(self.params['port'])

    @contextmanager
    def session(self):
        with closing(ftplib.FTP()) as session:
            session.connect(self.params['site'], self.params['port'])
            logger.debug('welcome message\n' + session.getwelcome())
            session.login(self.params['user'], self.params['password'])
            session.cwd(self.params['directory'])
            yield session

    def upload_file(self, session, path):
        target = os.path.basename(path)
        text_file = os.path.splitext(target)[1] in ('.txt', '.xml', '.html')
        if text_file and sys.version_info[0] < 3:
            mode = 'r'
        else:
            mode = 'rb'
        try:
            with open(path, mode) as f:
                if text_file:
                    session.storlines('STOR %s' % (target), f)
                else:
                    session.storbinary('STOR %s' % (target), f)
        except Exception as ex:
            return False, repr(ex)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
