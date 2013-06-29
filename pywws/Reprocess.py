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

"""Regenerate hourly and daily summary data
::

%s

Introduction
------------

This program recreates the calibrated, hourly, daily and monthly
summary data that is created by the :py:mod:`pywws.Process` program.
It should be run whenever you upgrade to a newer version of pywws (if
the summary data format has changed), change your calibration module
or alter your pressure offset.

Detailed API
------------

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.Reprocess [options] data_dir
 options are:
  -h | --help     display this help
  -v | --verbose  increase number of informative messages
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import os
import sys

from pywws import DataStore
from pywws.Logger import ApplicationLogger
from pywws import Process

def Reprocess(data_dir):
    # delete old format summary files
    print 'Deleting old summaries'
    for summary in ['calib', 'hourly', 'daily', 'monthly']:
        for root, dirs, files in os.walk(
                os.path.join(data_dir, summary), topdown=False):
            print root
            for file in files:
                os.unlink(os.path.join(root, file))
            os.rmdir(root)
    # create data summaries
    print 'Generating hourly and daily summaries'
    params = DataStore.params(data_dir)
    status = DataStore.status(data_dir)
    raw_data = DataStore.data_store(data_dir)
    calib_data = DataStore.calib_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    Process.Process(
        params, status,
        raw_data, calib_data, hourly_data, daily_data, monthly_data)
    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
            return 0
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    data_dir = args[0]
    return Reprocess(data_dir)

if __name__ == "__main__":
    sys.exit(main())
