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

"""Generate hourly, daily & monthly summaries of raw weather station
data
::

%s

This module takes raw weather station data (typically sampled every
five or ten minutes) and generates hourly, daily and monthly summary
data, which is useful when creating tables and graphs.

Before computing the data summaries, raw data is "calibrated" using a
user-programmable function. See :doc:`pywws.calib` for details.

The hourly data is derived from all the records in one hour, e.g. from
18:00:00 to 18:59:59, and is given the index of the last complete
record in that hour.

The daily data summarises the weather over a 24 hour period typically
ending at 2100 or 0900 hours, local (non DST) time, though midnight is
another popular convention. It is also indexed by the last complete
record in the period. Daytime and nighttime, as used when computing
maximum and minimum temperatures, are assumed to start at 0900 and
2100 local time, or 1000 and 2200 when DST is in effect, regardless of
the meteorological day.

To adjust the meteorological day to your preference, or that used by
your local official weather station, edit the "day end hour" line in
your ``weather.ini`` file, then run :mod:`pywws.reprocess` to regenerate
the summaries.

Monthly summary data is computed from the daily summary data. If the
meteorological day does not end at midnight, then each month may begin
and end up to 12 hours before or after midnight.

Wind speed data is averaged over the hour (or day) and the maximum
gust speed during the hour (or day) is recorded. The predominant wind
direction is calculated using vector arithmetic.

Rainfall is converted from the raw "total since last reset" figure to
a more useful total in the last hour, day or month.

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.process [options] data_dir
 options are:
  -h or --help     display this help
  -v or --verbose  increase number of informative messages
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

from ast import literal_eval
from collections import deque
from datetime import date, datetime, timedelta
import getopt
import logging
import math
import os
import sys

from pywws.calib import Calib
from pywws.constants import HOUR, DAY, SECOND
import pywws.logger
import pywws.storage
from pywws.timezone import time_zone

logger = logging.getLogger(__name__)

TIME_ERR = timedelta(seconds=45)
MINUTEx5 = timedelta(minutes=5)
HOURx3 = timedelta(hours=3)
WEEK = timedelta(days=7)


class Average(object):
    """Compute average of multiple data values."""
    def __init__(self):
        self.acc = 0.0
        self.count = 0

    def add(self, value):
        if value is None:
            return
        self.acc += value
        self.count += 1

    def result(self):
        if self.count == 0:
            return None
        return self.acc / float(self.count)


class Minimum(object):
    """Compute minimum value and timestamp of multiple data values."""
    def __init__(self):
        self.value = None
        self.time = None

    def add(self, value, time):
        if not self.time or value <= self.value:
            self.value = value
            self.time = time

    def result(self):
        if self.time:
            return self.value, self.time
        return None, None


class Maximum(object):
    """Compute maximum value and timestamp of multiple data values."""
    def __init__(self):
        self.value = None
        self.time = None

    def add(self, value, time):
        if not self.time or value > self.value:
            self.value = value
            self.time = time

    def result(self):
        if self.time:
            return self.value, self.time
        return None, None


sin_LUT = list(map(
    lambda x: math.sin(math.radians(float(x * 360) / 16.0)), range(16)))
cos_LUT = list(map(
    lambda x: math.cos(math.radians(float(x * 360) / 16.0)), range(16)))


class WindFilter(object):
    """Compute average wind speed and direction.

    The wind speed and direction of each data item is converted to a
    vector before averaging, so the result reflects the dominant wind
    direction during the time period covered by the data.

    Setting the ``decay`` parameter converts the filter from a simple
    averager to one where the most recent sample carries the highest
    weight, and earlier samples have a lower weight according to how
    long ago they were.

    This process is an approximation of "exponential smoothing". See
    `Wikipedia <http://en.wikipedia.org/wiki/Exponential_smoothing>`_
    for a detailed discussion.

    The parameter ``decay`` corresponds to the value ``(1 - alpha)``
    in the Wikipedia description. Because the weather data being
    smoothed may not be at regular intervals this parameter is the
    decay over 5 minutes. Weather data at other intervals will have
    its weight scaled accordingly.

    The return value is a (speed, direction) tuple.

    :param decay: filter coefficient decay rate.

    :type decay: float

    :rtype: (float, float)
    
    """
    def __init__(self, decay=1.0):
        self.decay = decay
        self.Ve = None
        self.Vn = 0.0
        self.total = 0.0
        self.weight = 1.0
        self.total_weight = 0.0
        self.last_idx = None

    def add(self, data):
        speed = data['wind_ave']
        if speed is None:
            return
        if self.last_idx and self.decay != 1.0:
            interval = data['idx'] - self.last_idx
            assert interval.days == 0
            decay = self.decay
            if interval != MINUTEx5:
                decay = decay ** (float(interval.seconds) /
                                  float(MINUTEx5.seconds))
            self.weight = self.weight / decay
        self.last_idx = data['idx']
        speed = speed * self.weight
        self.total += speed
        self.total_weight += self.weight
        direction = data['wind_dir']
        if direction is None:
            return
        if self.Ve is None:
            self.Ve = 0.0
        if isinstance(direction, int):
            self.Ve -= speed * sin_LUT[direction]
            self.Vn -= speed * cos_LUT[direction]
        else:
            direction = math.radians(float(direction) * 22.5)
            self.Ve -= speed * math.sin(direction)
            self.Vn -= speed * math.cos(direction)

    def result(self):
        if self.total_weight == 0.0:
            return (None, None)
        if self.Ve is None:
            return (self.total / self.total_weight, None)
        return (self.total / self.total_weight,
                (math.degrees(math.atan2(self.Ve, self.Vn)) + 180.0) / 22.5)


class HourAcc(object):
    """'Accumulate' raw weather data to produce hourly summary.

    Compute average wind speed and maximum wind gust, find dominant
    wind direction and compute total rainfall.

    """
    def __init__(self, last_rain):
        self.last_rain = last_rain
        self.copy_keys = ['idx', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
                          'abs_pressure', 'rel_pressure']
        self.reset()

    def reset(self):
        self.wind_fil = WindFilter()
        self.wind_gust = (-2.0, None)
        self.rain = 0.0
        self.retval = {}

    def add_raw(self, data):
        idx = data['idx']
        self.wind_fil.add(data)
        wind_gust = data['wind_gust']
        if wind_gust is not None and wind_gust > self.wind_gust[0]:
            self.wind_gust = (wind_gust, idx)
        rain = data['rain']
        if rain is not None:
            if self.last_rain is not None:
                diff = rain - self.last_rain
                if diff < -0.001:
                    logger.warning(
                        '%s rain reset %.1f -> %.1f', str(idx), self.last_rain, rain)
                elif diff > float(data['delay'] * 5):
                    # rain exceeds 5mm / minute, assume corrupt data and ignore it
                    logger.warning(
                        '%s rain jump %.1f -> %.1f', str(idx), self.last_rain, rain)
                else:
                    self.rain += max(0.0, diff)
            self.last_rain = rain
        # copy some current readings
        if 'illuminance' in data and not 'illuminance' in self.copy_keys:
            self.copy_keys.append('illuminance')
            self.copy_keys.append('uv')
        # if already have data to return, ignore 'lost contact' readings
        if data['temp_out'] is not None or not self.retval:
            for key in self.copy_keys:
                self.retval[key] = data[key]

    def result(self):
        if not self.retval:
            return None
        self.retval['wind_ave'], self.retval['wind_dir'] = self.wind_fil.result()
        if self.wind_gust[1]:
            self.retval['wind_gust'] = self.wind_gust[0]
        else:
            self.retval['wind_gust'] = None
        self.retval['rain'] = self.rain
        return self.retval


class DayAcc(object):
    """'Accumulate' weather data to produce daily summary.

    Compute average wind speed, maximum wind gust and daytime max &
    nighttime min temperatures, find dominant wind direction and
    compute total rainfall.

    Daytime is assumed to be 0900-2100 and nighttime to be 2100-0900,
    local time (1000-2200 and 2200-1000 during DST), regardless of the
    "day end hour" setting.

    """
    def __init__(self):
        self.has_illuminance = False
        self.ave = {}
        self.max = {}
        self.min = {}
        self.reset()

    def reset(self):
        self.wind_fil = WindFilter()
        self.wind_gust = (-1.0, None)
        self.rain = 0.0
        for i in ('temp_in', 'temp_out', 'hum_in', 'hum_out',
                  'abs_pressure', 'rel_pressure'):
            self.ave[i] = Average()
            self.max[i] = Maximum()
            self.min[i] = Minimum()
        for i in ('illuminance', 'uv'):
            self.ave[i] = Average()
            self.max[i] = Maximum()
        self.retval = dict()

    def add_raw(self, data):
        idx = data['idx']
        local_hour = time_zone.utc_to_nodst(idx).hour
        wind_gust = data['wind_gust']
        if wind_gust is not None and wind_gust > self.wind_gust[0]:
            self.wind_gust = (wind_gust, idx)
        for i in ('temp_in', 'temp_out'):
            temp = data[i]
            if temp is not None:
                self.ave[i].add(temp)
                if local_hour >= 9 and local_hour < 21:
                    # daytime max temperature
                    self.max[i].add(temp, idx)
                else:
                    # nighttime min temperature
                    self.min[i].add(temp, idx)
        for i in ('hum_in', 'hum_out', 'abs_pressure', 'rel_pressure'):
            value = data[i]
            if value is not None:
                self.ave[i].add(value)
                self.max[i].add(value, idx)
                self.min[i].add(value, idx)
        if 'illuminance' in data:
            self.has_illuminance = True
            for i in ('illuminance', 'uv'):
                value = data[i]
                if value is not None:
                    self.ave[i].add(value)
                    self.max[i].add(value, idx)

    def add_hourly(self, data):
        self.wind_fil.add(data)
        rain = data['rain']
        if rain is not None:
            self.rain += rain
        self.retval['idx'] = data['idx']

    def result(self):
        if not self.retval:
            return None
        self.retval['wind_ave'], self.retval['wind_dir'] = self.wind_fil.result()
        if self.wind_gust[1]:
            self.retval['wind_gust'] = self.wind_gust[0]
        else:
            self.retval['wind_gust'] = None
        self.retval['wind_gust_t'] = self.wind_gust[1]
        self.retval['rain'] = self.rain
        for i in ('temp_in', 'temp_out', 'hum_in', 'hum_out',
                  'abs_pressure', 'rel_pressure'):
            self.retval['%s_ave' % i] = self.ave[i].result()
            (self.retval['%s_max' % i],
             self.retval['%s_max_t' % i]) = self.max[i].result()
            (self.retval['%s_min' % i],
             self.retval['%s_min_t' % i]) = self.min[i].result()
        if self.has_illuminance:
            for i in ('illuminance', 'uv'):
                self.retval['%s_ave' % i] = self.ave[i].result()
                (self.retval['%s_max' % i],
                 self.retval['%s_max_t' % i]) = self.max[i].result()
        return self.retval


class MonthAcc(object):
    """'Accumulate' daily weather data to produce monthly summary.

    Compute daytime max & nighttime min temperatures.

    """
    def __init__(self, rain_day_threshold):
        self.rain_day_threshold = rain_day_threshold
        self.has_illuminance = False
        self.ave = {}
        self.min = {}
        self.max = {}
        self.min_lo = {}
        self.min_hi = {}
        self.min_ave = {}
        self.max_lo = {}
        self.max_hi = {}
        self.max_ave = {}
        self.reset()

    def reset(self):
        for i in ('temp_in', 'temp_out'):
            self.ave[i] = Average()
            self.min_lo[i] = Minimum()
            self.min_hi[i] = Maximum()
            self.min_ave[i] = Average()
            self.max_lo[i] = Minimum()
            self.max_hi[i] = Maximum()
            self.max_ave[i] = Average()
        for i in ('hum_in', 'hum_out', 'abs_pressure', 'rel_pressure'):
            self.ave[i] = Average()
            self.max[i] = Maximum()
            self.min[i] = Minimum()
        for i in ('illuminance', 'uv'):
            self.ave[i] = Average()
            self.max_lo[i] = Minimum()
            self.max_hi[i] = Maximum()
            self.max_ave[i] = Average()
        self.wind_fil = WindFilter()
        self.wind_gust = (-1.0, None)
        self.rain = 0.0
        self.rain_days = 0
        self.valid = False

    def add_daily(self, data):
        self.idx = data['idx']
        for i in ('temp_in', 'temp_out'):
            temp = data['%s_ave' % i]
            if temp is not None:
                self.ave[i].add(temp)
            temp = data['%s_min' % i]
            if temp is not None:
                self.min_lo[i].add(temp, data['%s_min_t' % i])
                self.min_hi[i].add(temp, data['%s_min_t' % i])
                self.min_ave[i].add(temp)
            temp = data['%s_max' % i]
            if temp is not None:
                self.max_lo[i].add(temp, data['%s_max_t' % i])
                self.max_hi[i].add(temp, data['%s_max_t' % i])
                self.max_ave[i].add(temp)
        for i in ('hum_in', 'hum_out', 'abs_pressure', 'rel_pressure'):
            value = data['%s_ave' % i]
            if value is not None:
                self.ave[i].add(value)
            value = data['%s_min' % i]
            if value is not None:
                self.min[i].add(value, data['%s_min_t' % i])
            value = data['%s_max' % i]
            if value is not None:
                self.max[i].add(value, data['%s_max_t' % i])
        self.wind_fil.add(data)
        wind_gust = data['wind_gust']
        if wind_gust is not None and wind_gust > self.wind_gust[0]:
            self.wind_gust = (wind_gust, data['wind_gust_t'])
        if 'illuminance_ave' in data:
            self.has_illuminance = True
            for i in ('illuminance', 'uv'):
                value = data['%s_ave' % i]
                if value is not None:
                    self.ave[i].add(value)
                value = data['%s_max' % i]
                if value is not None:
                    self.max_lo[i].add(value, data['%s_max_t' % i])
                    self.max_hi[i].add(value, data['%s_max_t' % i])
                    self.max_ave[i].add(value)
        self.rain += data['rain']
        if data['rain'] >= self.rain_day_threshold:
            self.rain_days += 1
        self.valid = True

    def result(self):
        if not self.valid:
            return None
        result = {}
        result['idx'] = self.idx
        result['rain'] = self.rain
        result['rain_days'] = self.rain_days
        for i in ('temp_in', 'temp_out'):
            result['%s_ave' % i] = self.ave[i].result()
            result['%s_min_ave' % i] = self.min_ave[i].result()
            (result['%s_min_lo' % i],
             result['%s_min_lo_t' % i]) = self.min_lo[i].result()
            (result['%s_min_hi' % i],
             result['%s_min_hi_t' % i]) = self.min_hi[i].result()
            result['%s_max_ave' % i] = self.max_ave[i].result()
            (result['%s_max_lo' % i],
             result['%s_max_lo_t' % i]) = self.max_lo[i].result()
            (result['%s_max_hi' % i],
             result['%s_max_hi_t' % i]) = self.max_hi[i].result()
        for i in ('hum_in', 'hum_out', 'abs_pressure', 'rel_pressure'):
            result['%s_ave' % i] = self.ave[i].result()
            (result['%s_max' % i],
             result['%s_max_t' % i]) = self.max[i].result()
            (result['%s_min' % i],
             result['%s_min_t' % i]) = self.min[i].result()
        result['wind_ave'], result['wind_dir'] = self.wind_fil.result()
        if self.wind_gust[1]:
            result['wind_gust'] = self.wind_gust[0]
        else:
            result['wind_gust'] = None
        result['wind_gust_t'] = self.wind_gust[1]
        if self.has_illuminance:
            for i in ('illuminance', 'uv'):
                result['%s_ave' % i] = self.ave[i].result()
                result['%s_max_ave' % i] = self.max_ave[i].result()
                (result['%s_max_lo' % i],
                 result['%s_max_lo_t' % i]) = self.max_lo[i].result()
                (result['%s_max_hi' % i],
                 result['%s_max_hi_t' % i]) = self.max_hi[i].result()
        return result


def calibrate_data(params, raw_data, calib_data):
    """'Calibrate' raw data, using a user-supplied function."""
    start = calib_data.before(datetime.max)
    if start is None:
        start = datetime.min
    start = raw_data.after(start + SECOND)
    if start is None:
        return start
    del calib_data[start:]
    calibrator = Calib(params, raw_data)
    def calibgen(inputdata):
        """Internal generator function"""
        count = 0
        for data in inputdata:
            idx = data['idx']
            count += 1
            if count % 10000 == 0:
                logger.info("calib: %s", idx.isoformat(' '))
            elif count % 500 == 0:
                logger.debug("calib: %s", idx.isoformat(' '))
            for key in ('rain', 'abs_pressure', 'temp_in'):
                if data[key] is None:
                    logger.error('Ignoring invalid data at %s', idx.isoformat(' '))
                    break
            else:
                yield calibrator.calib(data)
    calib_data.update(calibgen(raw_data[start:]))
    return start


def generate_hourly(calib_data, hourly_data, process_from):
    """Generate hourly summaries from calibrated data."""
    start = hourly_data.before(datetime.max)
    if start is None:
        start = datetime.min
    start = calib_data.after(start + SECOND)
    if process_from:
        if start:
            start = min(start, process_from)
        else:
            start = process_from
    if start is None:
        return start
    # set start of hour in local time (not all time offsets are integer hours)
    start = time_zone.hour_start(start)
    del hourly_data[start:]
    # preload pressure history, and find last valid rain
    prev = None
    pressure_history = deque()
    last_rain = None
    for data in calib_data[start - HOURx3:start]:
        if data['rel_pressure']:
            pressure_history.append((data['idx'], data['rel_pressure']))
        if data['rain'] is not None:
            last_rain = data['rain']
        prev = data
    # iterate over data in one hour chunks
    stop = calib_data.before(datetime.max)
    acc = HourAcc(last_rain)
    def hourlygen(inputdata, prev):
        """Internal generator function"""
        hour_start = start
        count = 0
        while hour_start <= stop:
            count += 1
            if count % 1008 == 0:
                logger.info("hourly: %s", hour_start.isoformat(' '))
            elif count % 24 == 0:
                logger.debug("hourly: %s", hour_start.isoformat(' '))
            hour_end = hour_start + HOUR
            acc.reset()
            for data in inputdata[hour_start:hour_end]:
                if data['rel_pressure']:
                    pressure_history.append((data['idx'], data['rel_pressure']))
                if prev:
                    err = data['idx'] - prev['idx']
                    if abs(err - timedelta(minutes=data['delay'])) > TIME_ERR:
                        logger.info('unexpected data interval %s %s',
                                    data['idx'].isoformat(' '), str(err))
                acc.add_raw(data)
                prev = data
            new_data = acc.result()
            if new_data and (new_data['idx'] - hour_start) >= timedelta(minutes=9):
                # compute pressure trend
                new_data['pressure_trend'] = None
                if new_data['rel_pressure']:
                    target = new_data['idx'] - HOURx3
                    while (len(pressure_history) >= 2 and
                           abs(pressure_history[0][0] - target) >
                           abs(pressure_history[1][0] - target)):
                        pressure_history.popleft()
                    if (pressure_history and
                            abs(pressure_history[0][0] - target) < HOUR):
                        new_data['pressure_trend'] = (
                            new_data['rel_pressure'] - pressure_history[0][1])
                # store new hourly data
                yield new_data
            hour_start = hour_end
    hourly_data.update(hourlygen(calib_data, prev))
    return start


def generate_daily(day_end_hour, use_dst,
                   calib_data, hourly_data, daily_data, process_from):
    """Generate daily summaries from calibrated and hourly data."""
    start = daily_data.before(datetime.max)
    if start is None:
        start = datetime.min
    start = calib_data.after(start + SECOND)
    if process_from:
        if start:
            start = min(start, process_from)
        else:
            start = process_from
    if start is None:
        return start
    # round to start of this day, in local time
    start = time_zone.day_start(start, day_end_hour, use_dst=use_dst)
    del daily_data[start:]
    stop = calib_data.before(datetime.max)
    acc = DayAcc()
    def dailygen(inputdata):
        """Internal generator function"""
        day_start = start
        count = 0
        while day_start <= stop:
            count += 1
            if count % 30 == 0:
                logger.info("daily: %s", day_start.isoformat(' '))
            else:
                logger.debug("daily: %s", day_start.isoformat(' '))
            day_end = day_start + DAY
            if use_dst:
                # day might be 23 or 25 hours long
                day_end = time_zone.day_start(
                    day_end + HOURx3, day_end_hour, use_dst=use_dst)
            acc.reset()
            for data in inputdata[day_start:day_end]:
                acc.add_raw(data)
            for data in hourly_data[day_start:day_end]:
                acc.add_hourly(data)
            new_data = acc.result()
            if new_data:
                new_data['start'] = day_start
                yield new_data
            day_start = day_end
    daily_data.update(dailygen(calib_data))
    return start


def generate_monthly(rain_day_threshold, day_end_hour, use_dst,
                     daily_data, monthly_data, process_from):
    """Generate monthly summaries from daily data."""
    start = monthly_data.before(datetime.max)
    if start is None:
        start = datetime.min
    start = daily_data.after(start + SECOND)
    if process_from:
        if start:
            start = min(start, process_from)
        else:
            start = process_from
    if start is None:
        return start
    # set start to noon on start of first day of month (local time)
    local_start = time_zone.utc_to_local(start).replace(tzinfo=None)
    local_start = local_start.replace(day=1, hour=12, minute=0, second=0)
    # go back to UTC and get start of day (which might be previous day)
    start = time_zone.local_to_utc(local_start)
    start = time_zone.day_start(start, day_end_hour, use_dst=use_dst)
    del monthly_data[start:]
    stop = daily_data.before(datetime.max)
    if stop is None:
        return None
    def monthlygen(inputdata, start, local_start):
        """Internal generator function"""
        acc = MonthAcc(rain_day_threshold)
        month_start = start
        count = 0
        while month_start <= stop:
            count += 1
            if count % 12 == 0:
                logger.info("monthly: %s", month_start.isoformat(' '))
            else:
                logger.debug("monthly: %s", month_start.isoformat(' '))
            if local_start.month < 12:
                local_start = local_start.replace(month=local_start.month+1)
            else:
                local_start = local_start.replace(
                    month=1, year=local_start.year+1)
            month_end = time_zone.local_to_utc(local_start)
            month_end = time_zone.day_start(
                month_end, day_end_hour, use_dst=use_dst)
            acc.reset()
            for data in inputdata[month_start:month_end]:
                acc.add_daily(data)
            new_data = acc.result()
            if new_data:
                new_data['start'] = month_start
                yield new_data
            month_start = month_end
    monthly_data.update(monthlygen(daily_data, start, local_start))
    return start


def get_day_end_hour(params):
    # get daytime end hour (in local time)
    day_end_hour, use_dst = literal_eval(
        params.get('config', 'day end hour', '9, False'))
    day_end_hour = day_end_hour % 24
    return day_end_hour, use_dst


def process_data(context):
    """Generate summaries from raw weather station data.

    The meteorological day end (typically 2100 or 0900 local time) is
    set in the preferences file ``weather.ini``. The default value is
    2100 (2200 during DST), following the historical convention for
    weather station readings.

    """
    logger.info('Generating summary data')
    # get time of last record
    last_raw = context.raw_data.before(datetime.max)
    if last_raw is None:
        raise IOError('No data found. Check data directory parameter.')
    # get daytime end hour (in local time)
    day_end_hour, use_dst = get_day_end_hour(context.params)
    # get other config
    rain_day_threshold = float(
        context.params.get('config', 'rain day threshold', '0.2'))
    # calibrate raw data
    start = calibrate_data(context.params, context.raw_data, context.calib_data)
    # generate hourly data
    start = generate_hourly(context.calib_data, context.hourly_data, start)
    # generate daily data
    start = generate_daily(day_end_hour, use_dst,
                           context.calib_data, context.hourly_data, context.daily_data, start)
    # generate monthly data
    generate_monthly(rain_day_threshold, day_end_hour, use_dst,
                     context.daily_data, context.monthly_data, start)
    return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print(__usage__.strip())
            return 0
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 1:
        print('Error: 1 argument required\n', file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 2
    pywws.logger.setup_handler(verbose)
    data_dir = args[0]
    with pywws.storage.pywws_context(data_dir) as context:
        return process_data(context)


if __name__ == "__main__":
    sys.exit(main())
