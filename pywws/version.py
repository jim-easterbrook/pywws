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

"""Compute version number(s) for pywws."""

from datetime import date
import subprocess

try:
    p = subprocess.Popen(
        ['git', 'rev-parse', '--short', 'HEAD'], stdout=subprocess.PIPE)
    commit = p.communicate()[0].strip().decode('ASCII')
    if p.returncode:
        commit = 'unknown'
except OSError:
    commit = 'unknown'
version = date.today().strftime('%y.%m')
release = '%s_%s' % (version, commit)

if __name__ == "__main__":
    print(release)
