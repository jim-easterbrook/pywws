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

"""Upload files to a web server by ftp or copy them to a local directory

This module uploads files to (typically) a website *via* ftp/sftp or
copies files to a local directory (e.g. if you are running pywws on the
web server). Details of the upload destination are stored in the file
``weather.ini`` in your data directory. The only way to set these
details is to edit the file. Run :py:mod:`pywws.towebsite` once to set
the default values, which you can then change. Here is what you're
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

"""

from __future__ import absolute_import, print_function

from contextlib import contextmanager
from datetime import timedelta
import logging
import os
import shutil
import sys

if sys.version_info[0] >= 3:
    from io import StringIO
else:
    from StringIO import StringIO

import pywws.logger
import pywws.service
import pywws.storage

__docformat__ = "restructuredtext en"
logger = logging.getLogger(__name__)


class _ftp(object):
    def __init__(self, site, user, password, directory, port):
        global ftplib
        import ftplib
        self.site = site
        self.user = user
        self.password = password
        self.directory = directory
        self.port = port

    @contextmanager
    def session(self):
        logger.info("Uploading to web site with FTP")
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.site, self.port)
        logger.debug('welcome message\n' + self.ftp.getwelcome())
        self.ftp.login(self.user, self.password)
        self.ftp.cwd(self.directory)
        try:
            yield None
        finally:
            self.ftp.close()

    def put(self, src, dest):
        text_file = os.path.splitext(src)[1] in ('.txt', '.xml', '.html')
        if text_file and sys.version_info[0] < 3:
            mode = 'r'
        else:
            mode = 'rb'
        with open(src, mode) as f:
            if text_file:
                self.ftp.storlines('STOR %s' % (dest), f)
            else:
                self.ftp.storbinary('STOR %s' % (dest), f)


class _sftp(object):
    def __init__(self, site, user, password, privkey, directory, port):
        global paramiko
        import paramiko
        self.site = site
        self.user = user
        self.password = password
        self.privkey = privkey
        self.directory = directory
        self.port = port

    @contextmanager
    def session(self):
        logger.info("Uploading to web site with SFTP")
        self.transport = paramiko.Transport((self.site, self.port))
        self.transport.start_client()
        if self.privkey:
            self.get_private_key(self.privkey)
            self.transport.auth_publickey(username=self.user, key=self.pkey)
        else:
            self.transport.auth_password(
                username=self.user, password=self.password)
        self.ftp = paramiko.SFTPClient.from_transport(self.transport)
        self.ftp.chdir(self.directory)
        try:
            yield None
        finally:
            self.ftp.close()
            self.transport.close()

    def put(self, src, dest):
        self.ftp.put(src, dest)

    def get_private_key(self, privkey):
        with open(privkey, 'r') as f:
            s = f.read()
        keyfile = StringIO(s)
        self.pkey = paramiko.RSAKey.from_private_key(keyfile)
        

class _copy(object):
    def __init__(self, directory):
        self.directory = directory

    @contextmanager
    def session(self):
        logger.info("Copying to local directory")
        if not os.path.isdir(self.directory):
            raise RuntimeError(
                'Directory "' + self.directory + '" does not exist.')
        yield None

    def put(self, src, dest):
        shutil.copy2(src, os.path.join(self.directory, dest))


class ToWebSite(object):
    catchup = -1
    interval = timedelta(seconds=150)
    logger = logger
    log_count = False
    service_name = 'pywws.towebsite'

    def __init__(self, context):
        params = context.params
        self.old_ex = None
        if eval(params.get('ftp', 'local site', 'False')):
            # copy to local directory
            directory = params.get(
                'ftp', 'directory',
                os.path.expanduser('~/public_html/weather/data/'))
            self.uploader = _copy(directory)
        else:
            # get remote site details
            site = params.get('ftp', 'site', 'ftp.username.your_isp.co.uk')
            user = params.get('ftp', 'user', 'username')
            # don't set a default password, as might use a private ssh key
            password = params.get('ftp', 'password', '')
            directory = params.get(
                'ftp', 'directory', 'public_html/weather/data/')
            if eval(params.get('ftp', 'secure', 'False')):
                port = eval(params.get('ftp', 'port', '22'))
                privkey = params.get('ftp', 'privkey')
                self.uploader = _sftp(
                    site, user, password, privkey, directory, port)
            else:
                port = eval(params.get('ftp', 'port', '21'))
                self.uploader = _ftp(site, user, password, directory, port)
        # create upload thread
        self.upload_thread = pywws.service.UploadThread(self, context)
        self.stop = self.upload_thread.stop

    @contextmanager
    def session(self):
        with self.uploader.session():
            yield None

    def upload_data(self, session, file='', delete=False):
        if os.path.isfile(file):
            target = os.path.basename(file)
            try:
                self.uploader.put(file, target)
            except Exception as ex:
                return False, str(ex)
            if delete:
                os.unlink(file)
        return True, 'OK'

    def upload(self, files, delete=False):
        if not files:
            return
        for file in files:
            self.upload_thread.queue.append(
                (None, {'file': file, 'delete': delete}))
        # start upload thread
        if not self.upload_thread.is_alive():
            self.upload_thread.start()


def main(argv=None):
    import argparse
    import inspect
    if argv is None:
        argv = sys.argv
    docstring = inspect.getdoc(sys.modules[__name__]).split('\n\n')
    parser = argparse.ArgumentParser(
        description=docstring[0], epilog=docstring[1])
    parser.add_argument('-v', '--verbose', action='count',
                        help='increase amount of reassuring messages')
    parser.add_argument('data_dir', help='root directory of the weather data')
    parser.add_argument('file', nargs='+', help='file to be uploaded')
    args = parser.parse_args(argv[1:])
    pywws.logger.setup_handler(args.verbose or 0)
    with pywws.storage.pywws_context(args.data_dir) as context:
        uploader = ToWebSite(context)
        uploader.upload(args.file)
        uploader.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
