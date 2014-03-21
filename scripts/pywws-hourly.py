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

"""Get weather data, process it, prepare graphs & text files, upload
to a web site and various weather services.

Typically run every hour from cron.
::

%s

This program does little more than call other modules in sequence to
get data from the weather station, process it, plot some graphs,
generate some text files and upload the results to the Internet.

For more information see :doc:`../guides/hourlylogging`.

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: %s [options] data_dir
 options are:
  -h or --help     display this help
  -v or --verbose  increase amount of reassuring messages
 data_dir is the root directory of the weather data (e.g. $(HOME)/weather/data)
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pywws.Hourly import main

__usage__ %= os.path.basename(__file__).rstrip('c')
__doc__ %= __usage__
__usage__ = __doc__.split('.')[0] + __usage__

if __name__ == "__main__":
    sys.exit(main())
