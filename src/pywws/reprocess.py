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

"""Regenerate hourly and daily summary data.

This module can also be run with the ``pywws-reprocess`` command. ::
%s
This module recreates the calibrated, hourly, daily and monthly
summary data that is created by the :py:mod:`pywws.process` module. It
should be run whenever you upgrade to a newer version of pywws (if the
summary data format has changed), change your calibration module or
alter your pressure offset.

The ``-u`` (or ``--update``) option is a special case. It should be
used when upgrading from any pywws version earlier than 14.02.dev1143.
Unlike normal reprocessing, the ``-u`` option changes your raw data.
You are advised to backup your data before using the ``-u`` option.

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: %s [options] data_dir
 options are:
  -h | --help     display this help
  -u | --update   update status on old data to include bits from wind_dir byte
  -v | --verbose  increase number of informative messages
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__ % ('python -m pywws.reprocess')

import getopt
import logging
import os
import sys

import pywws.logger
import pywws.process
import pywws.storage

logger = logging.getLogger(__name__)


def reprocess(data_dir, update):
    with pywws.storage.pywws_context(data_dir) as context:
        if update:
            logger.warning("Updating status to detect invalid wind_dir")
            count = 0
            raw_data = context.raw_data
            for data in raw_data[:]:
                count += 1
                idx = data['idx']
                if count % 10000 == 0:
                    logger.info("update: %s", idx.isoformat(' '))
                elif count % 500 == 0:
                    logger.debug("update: %s", idx.isoformat(' '))
                if data['wind_dir'] is not None and (data['wind_dir'] & 0x80):
                    data['wind_dir'] = None
                    raw_data[idx] = data
            raw_data.flush()
        # delete old format summary files
        logger.warning('Deleting old summaries')
        context.calib_data.clear()
        context.hourly_data.clear()
        context.daily_data.clear()
        context.monthly_data.clear()
        # create data summaries
        logger.warning('Generating hourly and daily summaries')
        pywws.process.process_data(context)
    return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv
    usage = (__usage__ % (argv[0])).strip()
    try:
        opts, args = getopt.getopt(
            argv[1:], "huv", ['help', 'update', 'verbose'])
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(usage, file=sys.stderr)
        return 1
    # process options
    update = False
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print(__doc__.split('\n\n')[0])
            print(usage)
            return 0
        elif o in ('-u', '--update'):
            update = True
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 1:
        print('Error: 1 argument required\n', file=sys.stderr)
        print(usage, file=sys.stderr)
        return 2
    pywws.logger.setup_handler(verbose)
    data_dir = args[0]
    return reprocess(data_dir, update)


if __name__ == "__main__":
    sys.exit(main())
