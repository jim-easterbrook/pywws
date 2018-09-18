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

"""Get weather data, store it, and process it.

Run this continuously, having set what tasks are to be done. This
script can also be run with the ``pywws-livelog`` command. ::
%s
For more information on using ``pywws.livelog``, see
:doc:`../guides/livelogging`.

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: %s [options] data_dir
 options are:
  -h      or --help      display this help
  -l file or --log file  write log information to file
  -v      or --verbose   increase amount of reassuring messages
 data_dir is the root directory of the weather data (e.g. ~/weather/data)
"""
__doc__ %= __usage__ % ('python -m pywws.livelog')

from datetime import datetime
import getopt
import logging
import os
import signal
import sys
import time

import pywws.localisation
import pywws.logdata
import pywws.logger
import pywws.process
import pywws.regulartasks
import pywws.storage

logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    if signum == signal.SIGTERM:
        raise KeyboardInterrupt
    if signum == signal.SIGHUP:
        raise NotImplementedError


def live_log(data_dir):
    # set up signal handlers
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    with pywws.storage.pywws_context(data_dir, live_logging=True) as context:
        # localise application
        pywws.localisation.set_application_language(context.params)
        # create a DataLogger object
        datalogger = pywws.logdata.DataLogger(context)
        # create a RegularTasks object
        tasks = pywws.regulartasks.RegularTasks(context)
        try:
            # fetch and process any new logged data
            datalogger.log_data()
            pywws.process.process_data(context)
            # get live data
            for data, logged in datalogger.live_data(
                                    logged_only=(not tasks.has_live_tasks())):
                if logged:
                    # process new data
                    pywws.process.process_data(context)
                    # do tasks
                    tasks.do_tasks()
                else:
                    tasks.do_live(data)
        except KeyboardInterrupt:
            return 0
        except NotImplementedError:
            return 3
        except Exception as ex:
            logger.exception(ex)
            return 1
    return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv
    usage = (__usage__ % (argv[0])).strip()
    try:
        opts, args = getopt.getopt(argv[1:], "hl:v", ['help', 'log=', 'verbose'])
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(usage, file=sys.stderr)
        return 1
    # process options
    logfile = None
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print(__doc__.split('\n\n')[0])
            print(usage)
            return 0
        elif o in ('-l', '--log'):
            logfile = a
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 1:
        print('Error: 1 argument required\n', file=sys.stderr)
        print(usage, file=sys.stderr)
        return 2
    pywws.logger.setup_handler(verbose, logfile)
    return live_log(args[0])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(str(e))
