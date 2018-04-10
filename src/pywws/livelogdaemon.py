#!/usr/bin/env python

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

"""Run 'live logging' as a UNIX daemon.

This script can also be run with the ``pywws-livelog-daemon`` command. ::
%s
Requires the python-daemon library.

If you get a "function() argument 1 must be code, not str" error, try
installing python-daemon from PyPI instead of your Linux repos.

For more information on 'live logging' see :doc:`../guides/livelogging`.

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: %s [options] data_dir log_file start|stop|restart
 options are:
  -h      or --help        display this help
  -p file or --pid file    store pid in 'file' (default /run/lock/pywws.pid)
  -v      or --verbose     increase amount of logging messages
 data_dir is the root directory of the weather data (e.g. ~/weather/data)
 log_file is a file to write logging to, e.g. /var/log/pywws.log
"""
__doc__ %= __usage__ % ('python -m pywws.livelogdaemon')

import getopt
import logging
import os
import sys

from daemon.daemon import DaemonContext
from daemon.runner import DaemonRunner, make_pidlockfile

import pywws.livelog
import pywws.logger

logger = logging.getLogger(__name__)

class PatchedDaemonRunner(DaemonRunner):
    # modify DaemonRunner to work with Python3
    def __init__(self, app):
        self.parse_args()
        self.app = app
        self.daemon_context = DaemonContext()
        self.daemon_context.stdin = open(app.stdin_path, 'rt')
        self.daemon_context.stdout = open(app.stdout_path, 'w+t')
        if sys.version_info[0] >= 3:
            self.daemon_context.stderr = open(
                    app.stderr_path, 'w+b', buffering=0)
        else:
            self.daemon_context.stderr = open(
                    app.stderr_path, 'w+t', buffering=0)

        self.pidfile = None
        if app.pidfile_path is not None:
            self.pidfile = make_pidlockfile(
                    app.pidfile_path, app.pidfile_timeout)
        self.daemon_context.pidfile = self.pidfile


class App(object):
    # attributes required by daemon runner
    stdin_path = '/dev/null'
    stdout_path = '/dev/null'
    stderr_path = '/dev/null'
    pidfile_path = '/run/lock/pywws.pid'
    pidfile_timeout = 5

    def __init__(self, argv):
        usage = (__usage__ % (argv[0])).strip()
        try:
            opts, args = getopt.getopt(
                argv[1:], "hp:v", ['help', 'pid=', 'verbose'])
        except getopt.error as msg:
            print('Error: %s\n' % msg, file=sys.stderr)
            print(usage, file=sys.stderr)
            sys.exit(1)
        # process options
        self.verbose = 0
        for o, a in opts:
            if o in ('-h', '--help'):
                print(__doc__.split('\n\n')[0])
                print(usage)
                sys.exit(0)
            elif o in ('-p', '--pid'):
                self.pidfile_path = os.path.abspath(a)
            elif o in ('-v', '--verbose'):
                self.verbose += 1
        # check arguments
        if len(args) != 3:
            print('Error: 3 arguments required\n', file=sys.stderr)
            print(usage, file=sys.stderr)
            sys.exit(2)
        self.data_dir = os.path.abspath(args[0])
        self.logfile = os.path.abspath(args[1])
        # leave remaining argument for daemon runner to parse
        sys.argv = [argv[0], args[2]]

    def run(self):
        pywws.logger.setup_handler(self.verbose, self.logfile)
        try:
            pywws.livelog.live_log(self.data_dir)
        except Exception as ex:
            logger.exception(ex)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    runner = PatchedDaemonRunner(App(argv))
    runner.do_action()
    return 0

if __name__ == "__main__":
    sys.exit(main())
