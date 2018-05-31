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


class SystemdFormatter(logging.Formatter):
    def format(self, record):
        level = min((68 - record.levelno) // 8, 7)
        return '<{:d}>{:s}'.format(
            level, super(SystemdFormatter, self).format(record))

    def formatException(self, exc_info):
        msg = super(SystemdFormatter, self).formatException(exc_info)
        return msg.replace('\n', '\\n')


class FilterURLLib3(object):
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        if (record.name == 'urllib3.connectionpool' and
                record.levelno < self.level + 1):
            return 0
        return 1


def setup_handler(verbose, logfile=None):
    root_logger = logging.getLogger('')
    if logfile=='systemd':
        level = logging.ERROR - (verbose * 10)
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = SystemdFormatter('%(name)s:%(message)s')
    elif logfile:
        level = logging.ERROR - (verbose * 10)
        handler = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=128*1024, backupCount=3)
        formatter = logging.Formatter(
            '%(asctime)s:%(name)s:%(message)s', '%Y-%m-%d %H:%M:%S')
    else:
        level = logging.WARNING - (verbose * 10)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s:%(name)s:%(message)s', '%H:%M:%S')
    level = max(level, 1)
    root_logger.setLevel(level)
    handler.addFilter(FilterURLLib3(level))
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    logger.warning(
        'pywws version %s, build %s (%s)', __version__, _release, _commit)
    logger.info('Python version %s', sys.version)
