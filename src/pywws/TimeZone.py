#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-15  pywws contributors

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

"""Provide a couple of :py:class:`datetime.tzinfo` compatible objects
representing local time and UTC.

Introduction
------------

This module provides two :py:class:`datetime.tzinfo` compatible objects
representing UTC and local time zones. These are used to convert
timestamps to and from UTC and local time. The weather station software
stores data with UTC timestamps, to avoid problems with daylight savings
time, but the template and plot programs output data with local times.

Detailed API
------------

"""

from datetime import datetime
import sys

import pytz
import tzlocal

from pywws.constants import HOUR

utc = pytz.utc
Local = tzlocal.get_localzone()

_now = datetime.now(tz=Local)
STDOFFSET = _now.utcoffset() - _now.dst()
del _now

def local_utc_offset(time):
    try:
        result = Local.utcoffset(time)
    except pytz.InvalidTimeError:
        result = Local.utcoffset(time + HOUR)
    except pytz.AmbiguousTimeError:
        result = Local.utcoffset(time - HOUR)
    return result

def main():
    print datetime.now().strftime('%Y/%m/%d %H:%M %Z')
    print datetime.now(utc).strftime('%Y/%m/%d %H:%M %Z')
    print datetime.now(Local).strftime('%Y/%m/%d %H:%M %Z')

if __name__ == "__main__":
    sys.exit(main())
