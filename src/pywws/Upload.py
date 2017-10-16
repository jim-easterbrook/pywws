#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-16  pywws contributors

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

"""Upload files to a web server by ftp or copy them to a local directory
::

%s

Introduction
------------

This module uploads files to (typically) a website *via* ftp/sftp or
copies files to a local directory (e.g. if you are running pywws on
the your web server). Details of the upload destination are stored in
the file ``weather.ini`` in your data directory. The only way to set
these details is to edit the file. Run :py:mod:`pywws.Upload` once to
set the default values, which you can then change. Here is what you're
likely to find when you edit ``weather.ini``::

  [ftp]
  secure = False
  directory = public_html/weather/data/
  local site = False
  password = secret
  site = ftp.username.your_isp.co.uk
  user = username

These are, I hope, fairly obvious. The ``local site`` option lets you
switch from uploading to a remote site to copying to a local site. If
you set ``local site = True`` then you can delete the ``secure``,
``site``, ``user`` and ``password`` lines.

``directory`` is the name of a directory in which all the uploaded
files will be put. This will depend on the structure of your web site
and the sort of host you use. Your hosting provider should be able to
tell you what ``site`` and ``user`` details to use. You should have
already chosen a ``password``.

The ``secure`` option lets you switch from normal ftp to sftp (ftp
over ssh). Some hosting providers offer this as a more secure upload
mechanism, so you should probably use it if available.

Detailed API
------------

"""

from __future__ import absolute_import

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.Upload [options] data_dir file [file...]
 options are:
  -h or --help    display this help
 data_dir is the root directory of the weather data
 file is a file to be uploaded

Login and ftp site details are read from the weather.ini file in
data_dir.
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import logging
import os
import shutil
import sys

from pywws import DataStore
from pywws.Logger import ApplicationLogger

class _ftp(object):
    def __init__(self, logger, site, user, password, directory, port):
        global ftplib
        import ftplib
        self.logger = logger
        self.site = site
        self.user = user
        self.password = password
        self.directory = directory
        self.port = port

    def connect(self):
        self.logger.info("Uploading to web site with FTP")
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.site, self.port)
        self.ftp.login(self.user, self.password)
        self.logger.debug(self.ftp.getwelcome())
        self.ftp.cwd(self.directory)

    def put(self, src, dest):
        text_file = os.path.splitext(src)[1] in ('.txt', '.xml', '.html')
        if text_file and sys.version_info[0] < 3:
            f = open(src, 'r')
        else:
            f = open(src, 'rb')
        if text_file:
            self.ftp.storlines('STOR %s' % (dest), f)
        else:
            self.ftp.storbinary('STOR %s' % (dest), f)
        f.close()

    def close(self):
        self.ftp.close()

class _sftp(object):
    def __init__(self, logger, site, user, password, privkey, directory, port):
        global paramiko
        import paramiko
        self.logger = logger
        self.site = site
        self.user = user
        self.password = password
        self.privkey = privkey
        self.directory = directory
        self.port = port

    def connect(self):
        self.logger.info("Uploading to web site with SFTP")
        self.transport = paramiko.Transport((self.site, self.port))
        self.transport.start_client()
        if self.privkey:
            self.get_private_key(self.privkey)
            self.transport.auth_publickey(username=self.user, key=self.pkey)
        else:
            self.transport.auth_password(username=self.user, password=self.password)
        self.ftp = paramiko.SFTPClient.from_transport(self.transport)
        self.ftp.chdir(self.directory)


    def put(self, src, dest):
        self.ftp.put(src, dest)

    def close(self):
        self.ftp.close()
        self.transport.close()

    def get_private_key(self, privkey):
        import StringIO
        f = open(privkey, 'r')
        s = f.read()
        keyfile = StringIO.StringIO(s)
        self.pkey = paramiko.RSAKey.from_private_key(keyfile)

        

class _copy(object):
    def __init__(self, logger, directory):
        self.logger = logger
        self.directory = directory

    def connect(self):
        self.logger.info("Copying to local directory")
        if not os.path.isdir(self.directory):
            raise RuntimeError(
                'Directory "' + self.directory + '" does not exist.')

    def put(self, src, dest):
        shutil.copy2(src, os.path.join(self.directory, dest))

    def close(self):
        pass

class Upload(object):
    def __init__(self, params):
        self.logger = logging.getLogger('pywws.Upload')
        self.params = params
        self.old_ex = None
        if eval(self.params.get('ftp', 'local site', 'False')):
            # copy to local directory
            directory = self.params.get(
                'ftp', 'directory',
                os.path.expanduser('~/public_html/weather/data/'))
            self.uploader = _copy(self.logger, directory)
        else:
            # get remote site details
            site = self.params.get('ftp', 'site', 'ftp.username.your_isp.co.uk')
            user = self.params.get('ftp', 'user', 'username')
            # we don't set a default password, as we might use a private ssh key 
            if self.params.get('ftp','password'):
                password = self.params.get('ftp', 'password')
            else:
                password = ''
            directory = self.params.get(
                'ftp', 'directory', 'public_html/weather/data/')
            if eval(self.params.get('ftp', 'secure', 'False')):
                port = eval(self.params.get('ftp', 'port', '22'))
                privkey = self.params.get('ftp', 'privkey')
                self.uploader = _sftp(
                    self.logger, site, user, password, privkey, directory, port)
            else:
                port = eval(self.params.get('ftp', 'port', '21'))
                self.uploader = _ftp(
                    self.logger, site, user, password, directory, port)

    def connect(self):
        try:
            self.uploader.connect()
        except Exception, ex:
            e = str(ex)
            if e == self.old_ex:
                self.logger.debug(e)
            else:
                self.logger.error(e)
                self.old_ex = e
            return False
        return True

    def upload_file(self, file):
        target = os.path.basename(file)
        try:
            self.uploader.put(file, target)
            return True
        except Exception, ex:
            e = str(ex)
            if e == self.old_ex:
                self.logger.debug(e)
            else:
                self.logger.error(e)
                self.old_ex = e
        return False

    def disconnect(self):
        self.uploader.close()

    def upload(self, files):
        if not self.connect():
            return False
        OK = True
        for file in files:
            if not self.upload_file(file):
                OK = False
                break
        self.disconnect()
        return OK

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
            return 0
    # check arguments
    if len(args) < 2:
        print >>sys.stderr, "Error: at least 2 arguments required"
        print >>sys.stderr, __usage__.strip()
        return 2
    logger = ApplicationLogger(1)
    if Upload(DataStore.params(args[0])).upload(args[1:]):
        return 0
    return 3

if __name__ == "__main__":
    sys.exit(main())
