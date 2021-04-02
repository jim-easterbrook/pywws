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

import datetime
import logging
import sys

import tzlocal

from pywws.constants import DAY, HOUR

logger = logging.getLogger(__name__)


class _TimeZone(object):
    class _UTC(datetime.tzinfo):
        _offset = datetime.timedelta(0)

        def utcoffset(self, dt):
            return self._offset

        def dst(self, dt):
            return self._offset

        def tzname(self, dt):
            return 'UTC'


    def __init__(self, tz_name=None):
        if tz_name:
            # use a named time zone instead of system default, for testing
            import pytz
            self.local = pytz.timezone(tz_name)
        else:
            self.local = tzlocal.get_localzone()
        logger.info('Using timezone "{!s}"'.format(self.local))
        self._using_pytz = hasattr(self.local, 'localize')
        if sys.version_info >= (3, 2):
            self.utc = datetime.timezone.utc
        else:
            self.utc = self._UTC()

    def local_to_utc(self, dt):
        """Convert a local time (with or without tzinfo) to UTC without
        tzinfo, as used for pywws timestamps."""
        if dt.tzinfo is None:
            if self._using_pytz:
                dt = self.local.localize(dt)
            else:
                dt = dt.replace(tzinfo=self.local)
        return dt.astimezone(self.utc).replace(tzinfo=None)

    def utc_to_local(self, dt):
        """Convert a pywws time to local time, with tzinfo."""
        return dt.replace(tzinfo=self.utc).astimezone(self.local)

    def utc_to_nodst(self, dt):
        """Convert a pywws time to local time, without DST.

        This could be an invalid time, so no tzinfo is included."""
        dt = self.utc_to_local(dt)
        return dt.replace(tzinfo=None) - dt.dst()

    def hour_start(self, dt):
        """Return UTC time before dt whose local time is on the hour."""
        local = self.utc_to_local(dt)
        diff = local - local.replace(minute=0, second=0)
        return dt - diff

    def day_start(self, dt, day_end_hour, use_dst=True):
        """Return UTC time before dt whose local time is day_end_hour.

        If use_dst is False then DST is ignored, so a day ending at 9am
        (local time) in winter would end at 10am in summer."""
        # get UTC and local equivalent
        dt = dt.replace(tzinfo=self.utc)
        local = dt.astimezone(self.local)
        if not use_dst:
            local = local.replace(tzinfo=None) - local.dst()
        # truncate to the hour
        diff = local - local.replace(minute=0, second=0)
        dt -= diff
        local -= diff
        # decrement UTC until equivalent local time has correct hour
        for h in range(4):
            hours = local.hour - day_end_hour
            if hours == 0:
                break
            elif hours > 1:
                hours -= 1
            elif hours < 0:
                hours += 23
            dt -= HOUR * hours
            local = dt.astimezone(self.local)
            if not use_dst:
                local = local.replace(tzinfo=None) - local.dst()
        return dt.replace(tzinfo=None)

    def _dst_transitions(self):
        """Find local times near DST transitions in the last year.

        This is only intended to be used for testing."""
        day = datetime.datetime.now(tz=self.local).replace(
            minute=15, second=0, microsecond=0)
        dst = day.dst()
        for d in range(365):
            day -= DAY
            if self._using_pytz:
                day = self.local.normalize(day)
            if day.dst() == dst:
                continue
            hour = day
            for h in range(25):
                hour += HOUR
                if self._using_pytz:
                    hour = self.local.normalize(hour)
                if hour.dst() == dst:
                    yield hour
                    break
            dst = day.dst()


time_zone = _TimeZone()


def main():
    global time_zone
    if len(sys.argv) > 1:
        time_zone = _TimeZone(sys.argv[1])
    print('Local time zone:', time_zone.local)
    now = datetime.datetime.utcnow().replace(microsecond=0)
    print('UTC time:', now)
    lcl = time_zone.utc_to_local(now)
    print('Local time:', lcl, lcl.strftime('(%Z)'))
    print()
    print('most recent 9am', time_zone.day_start(now, 9), 'UTC')
    print('most recent 9pm', time_zone.day_start(now, 21), 'UTC')
    for dt in time_zone._dst_transitions():
        print()
        print('Convert local to UTC around DST transition')
        lcl = dt.replace(tzinfo=None)
        lcl -= HOUR * 2
        for h in range(4):
            utc = time_zone.local_to_utc(lcl)
            print(lcl, '->', utc)
            lcl += HOUR
        print()
        print('Convert UTC to local around DST transition')
        utc -= HOUR * 3
        for h in range(4):
            lcl = time_zone.utc_to_local(utc)
            print(utc, '->', lcl, lcl.strftime('(%Z)'))
            utc += HOUR
    return 0


if __name__ == "__main__":
    sys.exit(main())
