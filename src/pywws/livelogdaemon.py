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

"""Run 'live logging' as a UNIX daemon.

This script can also be run with the ``pywws-livelog-daemon`` command. ::
%s
Requires the python-daemon library.

If you get a "function() argument 1 must be code, not str" error, try
installing python-daemon from PyPI instead of your Linux repos.

For more information on 'live logging' see :doc:`../guides/livelogging`.

"""

from __future__ import absolute_import

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

from daemon.runner import DaemonRunner
import getopt
import os
import sys

from pywws.LiveLog import LiveLog
from pywws.Logger import ApplicationLogger

class Runner(DaemonRunner):
    def __init__(self, data_dir, action, files_preserve, pid_file):
        self.data_dir = os.path.abspath(data_dir)
        # attributes required by daemon runner
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path = pid_file
        self.pidfile_timeout = 5
        # initialise daemon runner
        DaemonRunner.__init__(self, self)
        self.daemon_context.files_preserve = files_preserve
        self.daemon_context.initgroups = False
        self.action = action

    def parse_args(self, argv=None):
        # don't let daemon runner do its own command line parsing
        pass

    def run(self):
        LiveLog(self.data_dir)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    usage = (__usage__ % (argv[0])).strip()
    try:
        opts, args = getopt.getopt(
            argv[1:], "hp:v", ['help', 'pid=', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, usage
        return 1
    # process options
    pid_file = '/run/lock/pywws.pid'
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print __doc__.split('\n\n')[0]
            print usage
            return 0
        elif o in ('-p', '--pid'):
            pid_file = a
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 3:
        print >>sys.stderr, 'Error: 3 arguments required\n'
        print >>sys.stderr, usage
        return 2
    logger = ApplicationLogger(verbose, args[1])
    runner = Runner(
        args[0], args[2], map(lambda x: x.stream, logger.handlers), pid_file)
    try:
        runner.do_action()
    except Exception, ex:
        logger.exception(ex)
        return 3
    return 0

if __name__ == "__main__":
    sys.exit(main())
