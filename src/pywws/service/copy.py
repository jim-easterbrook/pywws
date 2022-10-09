# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-22  pywws contributors

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

"""Copy files to another directory.

This module can be used to copy template and graph results to another
directory on your computer. This could be useful if you are running a
web server on the same machine as pywws (or on a machine that's
accessible as a network share).

* Example ``weather.ini`` configuration::

    [copy]
    directory = /home/www/public_html/weather/data/

    [hourly]
    plot = ['24hrs.png.xml', 'rose_12hrs.png.xml']
    text = ['24hrs.txt']
    services = [('copy', '24hrs.txt', '24hrs.png', 'rose_12hrs.png')]

Run :py:mod:`pywws.service.copy` once to set the default configuration,
which you can then change. ``directory`` is the full path of a directory
in which all the copied files will be put.

You can copy any files you like, as often as you like, but typical usage
is to update a website once an hour. Each file to be uploaded needs to
be listed in a service entry like ``('copy', 'filename')``. If the file
is not in your ``work`` directory's ``output`` directory then
``filename`` should be the full path.

If you need to copy some files to a different directory you can copy the
:py:mod:`pywws.service.copy` module to your ``modules`` directory,
making sure that you rename it, for example to ``copy2.py``. This
creates a ``copy2`` service that you can use in the same way, but with a
different ``directory``.

"""

from __future__ import absolute_import

from contextlib import contextmanager
from datetime import timedelta
import logging
import os
import shutil
import sys

import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.FileService):
    config = {'directory'  : ('', True,  None)}
    logger = logger
    service_name = service_name

    @contextmanager
    def session(self):
        yield None, 'OK'

    def upload_file(self, session, path):
        try:
            if not os.path.isdir(self.params['directory']):
                os.makedirs(self.params['directory'])
            shutil.copy(path, self.params['directory'])
        except Exception as ex:
            return False, repr(ex)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
