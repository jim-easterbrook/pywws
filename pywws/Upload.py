#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

def Upload(params, files):
    logger = logging.getLogger('pywws.Upload')
    if eval(params.get('ftp', 'local site', 'False')):
        logger.info("Copying to local directory")
        # copy to local directory
        directory = params.get(
            'ftp', 'directory', os.path.expanduser('~/public_html/weather/data/'))
        if not os.path.isdir(directory):
            os.makedirs(directory)
        for file in files:
            shutil.copy2(file, directory)
        return True
    logger.info("Uploading to web site")
    # get remote site details
    secure = eval(params.get('ftp', 'secure', 'False'))
    site = params.get('ftp', 'site', 'ftp.username.your_isp.co.uk')
    user = params.get('ftp', 'user', 'username')
    password = params.get('ftp', 'password', 'secret')
    directory = params.get('ftp', 'directory', 'public_html/weather/data/')
    # open connection
    if secure:
        import paramiko
        try:
            transport = paramiko.Transport((site, 22))
            transport.connect(username=user, password=password)
            ftp = paramiko.SFTPClient.from_transport(transport)
            ftp.chdir(directory)
        except Exception, ex:
            logger.error(str(ex))
            return False
    else:
        import ftplib
        try:
            ftp = ftplib.FTP(site, user, password)
            logger.debug(ftp.getwelcome())
            ftp.cwd(directory)
        except Exception, ex:
            logger.error(str(ex))
            return False
    OK = True
    for file in files:
        target = os.path.basename(file)
        text_file = os.path.splitext(file)[1] in ('.txt', '.xml', '.html')
        # have three tries before giving up
        for n in range(3):
            try:
                if secure:
                    ftp.put(file, target)
                else:
                    if text_file and sys.version_info[0] < 3:
                        f = open(file, 'r')
                    else:
                        f = open(file, 'rb')
                    if text_file:
                        ftp.storlines('STOR %s' % (target), f)
                    else:
                        ftp.storbinary('STOR %s' % (target), f)
                    f.close()
                break
            except Exception, ex:
                logger.error(str(ex))
        else:
            OK = False
            break
    ftp.close()
    if secure:
        transport.close()
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
    if Upload(DataStore.params(args[0]), args[1:]):
        return 0
    return 3

if __name__ == "__main__":
    sys.exit(main())
