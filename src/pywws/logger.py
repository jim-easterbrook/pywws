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

"""Configure Python logging system"""

from __future__ import absolute_import

import logging
import logging.handlers
import sys

from pywws import __version__, _release, _commit

logger = logging.getLogger(__name__)

def setup_handler(verbose, logfile=None):
    root_logger = logging.getLogger('')
    if logfile:
        root_logger.setLevel(max(logging.ERROR - (verbose * 10), 1))
        handler = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=128*1024, backupCount=3)
        datefmt = '%Y-%m-%d %H:%M:%S'
    else:
        root_logger.setLevel(max(logging.WARNING - (verbose * 10), 1))
        handler = logging.StreamHandler()
        datefmt = '%H:%M:%S'
    handler.setFormatter(
        logging.Formatter('%(asctime)s:%(name)s:%(message)s', datefmt))
    root_logger.addHandler(handler)
    logger.warning(
        'pywws version %s, build %s (%s)', __version__, _release, _commit)
    logger.info('Python version %s', sys.version)
