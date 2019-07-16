# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-19  pywws contributors

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

"""Upload files to a web server by SFTP.

This module uploads files to (typically) a website *via* SFTP. Details
of the upload destination are stored in the file ``weather.ini`` in your
data directory. You should be able to get the required information from
your web space provider. If your provider doesn't allow SFTP then use
:py:mod:`pywws.service.ftp` instead.

* Additional dependency: https://www.paramiko.org/ v2.1.0 or later
* Example ``weather.ini`` configuration::

    [sftp]
    site = ftp.xxxx.yyyy.co.uk
    user = xxxxxxx
    directory = public_html/weather/data/
    port = 22
    password =
    privkey = /home/pywws/.ssh/webhost_rsa

    [hourly]
    plot = ['24hrs.png.xml', 'rose_12hrs.png.xml']
    text = ['24hrs.txt']
    services = [('sftp', '24hrs.txt', '24hrs.png', 'rose_12hrs.png')]

Paramiko can be installed with ``pip``::

    sudo pip install paramiko

Run :py:mod:`pywws.service.sftp` once to set the default configuration,
which you can then change. ``directory`` is the name of a directory in
which all the uploaded files will be put. This will depend on the
structure of your web site and the sort of host you use. ``port`` is the
port number to use. 22 is the standard value but your web space provider
may require a different port.

Authentication can be by password or RSA public key. To use a key you
first need to create a passwordless key pair using ``ssh-keygen``, then
copy the public key to your web space provider. For example::

    ssh-keygen -t rsa -f webhost_rsa
    ssh-copy-id -i webhost_rsa.pub xxxxxxx@ftp.xxxx.yyyy.co.uk

Move both key files to somewhere convenient, such as
``/home/pywws/.ssh/`` and set ``privkey`` to the full path of the
private key.

You can upload any files you like, as often as you like, but typical
usage is to update a website once an hour. Each file to be uploaded
needs to be listed in a service entry like ``('sftp', 'filename')``. If
the file is not in your ``work`` directory's ``output`` directory then
``filename`` should be the full path.

"""

from __future__ import absolute_import

from contextlib import contextmanager
from datetime import timedelta
import logging
import os
import sys

import paramiko

import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.FileService):
    config = {
        'site'       : ('',   True,  None),
        'user'       : ('',   True,  None),
        'password'   : ('',   False, None),
        'directory'  : ('',   True,  None),
        'port'       : ('22', True,  None),
        'privkey'    : ('',   False, None),
        }
    logger = logger
    service_name = service_name

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        self.params['port'] = int(self.params['port'])
        if self.params['privkey']:
            self.params['privkey'] = paramiko.RSAKey.from_private_key_file(
                self.params['privkey'])

    @contextmanager
    def session(self):
        logger.info("Uploading to web site with SFTP")
        address = (self.params['site'], self.params['port'])
        with paramiko.Transport(address) as transport:
            transport.start_client(timeout=30)
            if self.params['privkey']:
                transport.auth_publickey(username=self.params['user'],
                                         key=self.params['privkey'])
            else:
                transport.auth_password(username=self.params['user'],
                                        password=self.params['password'])
            with paramiko.SFTPClient.from_transport(transport) as session:
                session.get_channel().settimeout(20)
                session.chdir(self.params['directory'])
                yield session

    def upload_file(self, session, path):
        target = os.path.basename(path)
        try:
            session.put(path, target)
        except Exception as ex:
            return False, repr(ex)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
