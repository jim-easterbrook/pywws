#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-21  pywws contributors

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

from __future__ import print_function

from datetime import datetime, timedelta
import logging
import sys

import pytz
import tzlocal

from pywws.constants import DAY, HOUR

logger = logging.getLogger(__name__)


class TimeZone(object):
    def __init__(self, tz_name=None):
        if tz_name:
            self.local = pytz.timezone(tz_name)
        else:
            self.local = tzlocal.get_localzone()
        logger.info('Using timezone "{!s}"'.format(self.local))
        self.utc = pytz.utc
        now = datetime.utcnow().replace(day=15, hour=12)
        while self.dst(now):
            now -= timedelta(days=30)
        self.standard_offset = self.utcoffset(now)

    def dst(self, dt):
        if sys.version_info < (3, 6):
            return self.local.dst(dt, is_dst=False)
        return self.local.dst(dt)

    def utcoffset(self, dt):
        if sys.version_info < (3, 6):
            return self.local.utcoffset(dt, is_dst=False)
        return self.local.utcoffset(dt)

    def localize(self, dt):
        """Attach local timezone to a naive timestamp with no adjustment."""
        if sys.version_info < (3, 6):
            return self.local.localize(dt)
        return dt.replace(tzinfo=self.local)

    def to_local(self, dt):
        """Convert any timestamp to local time (with tzinfo)."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.utc)
        return dt.astimezone(self.local)

    def to_utc(self, dt):
        """Convert any timestamp to UTC (with tzinfo)."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.utc)
        return dt.astimezone(self.utc)

    def to_naive(self, dt):
        """Convert any timestamp to pywws (utc, no tzinfo)."""
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(self.utc).replace(tzinfo=None)

    def local_replace(self, dt, use_dst=True, _recurse=False, **kwds):
        """Return pywws timestamp (utc, no tzinfo) for the most recent
        local time before the pywws timestamp dt, with datetime replace
        applied.

        """
        local_time = dt + self.standard_offset
        if use_dst:
            dst_offset = self.dst(local_time)
            if dst_offset:
                local_time += dst_offset
                adjusted_time = local_time.replace(**kwds)
                if adjusted_time > local_time and not _recurse:
                    return self.local_replace(
                        dt - DAY, use_dst=use_dst, _recurse=True, **kwds)
                adjusted_time -= dst_offset
                if self.dst(adjusted_time):
                    return adjusted_time - self.standard_offset
        adjusted_time = local_time.replace(**kwds)
        if use_dst:
            dst_offset = self.dst(adjusted_time)
            adjusted_time -= dst_offset
        if adjusted_time > local_time and not _recurse:
            return self.local_replace(
                dt - DAY, use_dst=use_dst, _recurse=True, **kwds)
        return adjusted_time - self.standard_offset

    def local_midnight(self, dt):
        """Return pywws timestamp (utc, no tzinfo) for the local time
        midnight before the supplied pywws timestamp.

        """
        return self.local_replace(dt, hour=0, minute=0, second= 0)


timezone = TimeZone()


def main():
    now = datetime.utcnow().replace(microsecond=0)
    print('using timezone', timezone.local)
    print('current time')
    print(now, 'UTC')
    lcl = timezone.to_local(now)
    print(lcl, lcl.strftime('%Z'))
    now_utc = timezone.to_utc(lcl)
    print(now_utc, now_utc.strftime('%Z'))
    print()
    print('most recent 9am',
          timezone.local_replace(now, hour=9, minute=0, second=0), 'UTC')
    print('most recent 9pm',
          timezone.local_replace(now, hour=21, minute=0, second=0), 'UTC')
    print()
    print('Ambiguous / missing times in "Europe/London"')
    tz = TimeZone('Europe/London')
    dt = datetime(2020, 3, 28, 23, 15)
    for hour in range(4):
        lcl = tz.to_local(dt)
        print(dt, 'UTC =', lcl, lcl.strftime('%Z'))
        dt += HOUR
    print()
    dt = datetime(2020, 10, 24, 23, 15)
    for hour in range(4):
        lcl = tz.to_local(dt)
        print(dt, 'UTC =', lcl, lcl.strftime('%Z'))
        dt += HOUR
    print()
    print('DST transitions in "America/St_Johns"')
    tz = TimeZone('America/St_Johns')
    for day in range(11, 13):
        dt = datetime(2018, 3, day, 12)
        mn = tz.local_midnight(dt)
        lcl = tz.to_local(mn)
        print('midnight', mn, 'UTC', lcl, lcl.strftime('%Z'))
    print()
    for day in range(4, 6):
        dt = datetime(2018, 11, day, 12)
        mn = tz.local_midnight(dt)
        lcl = tz.to_local(mn)
        print('midnight', mn, 'UTC', lcl, lcl.strftime('%Z'))


if __name__ == "__main__":
    sys.exit(main())
