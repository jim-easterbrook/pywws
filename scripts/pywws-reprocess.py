#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-14  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

This program recreates the calibrated, hourly, daily and monthly
summary data that is created by the :py:mod:`pywws.Process` module. It
should be run whenever you upgrade to a newer version of pywws (if the
summary data format has changed), change your calibration module or
alter your pressure offset.

The ``-u`` (or ``--update``) option is a special case. It should be
used when upgrading from any pywws version earlier than 14.02.dev1143.
Unlike normal reprocessing, the ``-u`` option changes your raw data.
You are advised to backup your data before using the ``-u`` option.

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: %s [options] data_dir
 options are:
  -h | --help     display this help
  -u | --update   update status on old data to include bits from wind_dir byte
  -v | --verbose  increase number of informative messages
 data_dir is the root directory of the weather data
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pywws.Reprocess import main

__usage__ %= os.path.basename(__file__).rstrip('c')
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

if __name__ == "__main__":
    sys.exit(main())
