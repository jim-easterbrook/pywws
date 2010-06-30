#!/usr/bin/env python
"""
Generate hourly, daily & monthly summaries of raw weather station data.

usage: python Process.py [options] data_dir
options are:
\t--help\t\tdisplay this help
data_dir is the root directory of the weather data
"""

from collections import deque
from datetime import date, datetime, timedelta
import getopt
import os
import sys

import DataStore
from TimeZone import Local, utc
import WeatherStation

class Record:
    pass
class Average:
    def __init__(self):
        self.acc = 0.0
        self.count = 0
    def add(self, value):
        if value == None:
            return
        self.acc += value
        self.count += 1
    def result(self):
        if self.count == 0:
            return None
        return self.acc / float(self.count)
class MinTemp:
    def __init__(self):
        self.value = 1000.0
        self.time = None
    def add(self, value, time):
        if value <= self.value:
            self.value = value
            self.time = time
    def result(self):
        if self.time:
            return self.value, self.time
        return None, None
class MaxTemp:
    def __init__(self):
        self.value = -1000.0
        self.time = None
    def add(self, value, time):
        if value > self.value:
            self.value = value
            self.time = time
    def result(self):
        if self.time:
            return self.value, self.time
        return None, None
class Acc:
    """'Accumulate' raw weather data to produce summaries.

    Compute average wind speed, log daytime max & nighttime min
    temperatures and maximum wind gust, find dominant wind direction
    and compute total rainfall.

    Daytime is assumed to be 0900-2100 and nighttime to be 2100-0900,
    local time (1000-2200 and 2200-1000 during DST), regardless of the
    "day end hour" setting."""
    def __init__(self, time_offset, last_rain):
        self.last_rain = last_rain
        self.h_wind_dir = {}
        self.d_wind_dir = {}
        self.reset_daily()
        self.reset_hourly()
        # divide 24 hours of UTC day into day and night
        self._daytime = []
        for i in range(24):
            self._daytime.append(True)
        night_hour = (21 - (time_offset.seconds / 3600)) % 24
        for i in range(12):
            self._daytime[night_hour] = False
            night_hour = (night_hour + 1) % 24
    def add(self, raw):
        """Add a raw data reading."""
        idx = raw['idx']
        wind_ave = raw['wind_ave']
        if wind_ave != None:
            wind_dir = raw['wind_dir']
            if wind_dir != None and wind_dir < 16:
                self.h_wind_dir[wind_dir] += wind_ave
            self.h_wind_acc += wind_ave
            self.h_wind_count += 1
        wind_gust = raw['wind_gust']
        if wind_gust != None and \
           wind_gust > self.h_wind_gust[0]:
            self.h_wind_gust = (wind_gust, idx)
        rain = raw['rain']
        if rain != None:
            if self.last_rain != None:
                diff = rain - self.last_rain
                if diff < -0.001:
                    print '%s rain reset %.1f -> %.1f' % (
                        idx, self.last_rain, rain)
                else:
                    self.h_rain += diff
            self.last_rain = rain
        for i in ('in', 'out'):
            temp = raw['temp_%s' % i]
            if temp != None:
                self.d_temp[i].ave.add(temp)
                if self._daytime[idx.hour]:
                    # daytime max temperature
                    self.d_temp[i].max.add(temp, idx)
                else:
                    # nightime min temperature
                    self.d_temp[i].min.add(temp, idx)
        self.h_valid = True
    def reset_hourly(self):
        for i in range(16):
            self.h_wind_dir[i] = 0.0
        self.h_wind_acc = 0.0
        self.h_wind_gust = (-2.0, None)
        self.h_rain = 0.0
        self.h_wind_count = 0
        self.h_valid = False
    def get_hourly(self):
        """Get the hourly result of the data accumulation."""
        if not self.h_valid:
            self.reset_hourly()
            return None
        retval = {}
        if self.h_wind_count > 0:
            best = 0
            for dir, val in self.h_wind_dir.items():
                if val > self.h_wind_dir[best]:
                    best = dir
            retval['wind_dir'] = best
            wind_ave = self.h_wind_acc / self.h_wind_count
            wind_ave = float(int(wind_ave * 100)) / 100.0
            retval['wind_ave'] = wind_ave
        else:
            retval['wind_dir'] = None
            retval['wind_ave'] = None
        if self.h_wind_gust[1]:
            retval['wind_gust'] = self.h_wind_gust[0]
        else:
            retval['wind_gust'] = None
        retval['rain'] = self.h_rain
        # update daily data before resetting hourly data
        if self.h_wind_count > 0:
            for i in range(16):
                self.d_wind_dir[i] += self.h_wind_dir[i]
            self.d_wind_acc += self.h_wind_acc
            self.d_wind_count += self.h_wind_count
        if self.h_wind_gust[0] > self.d_wind_gust[0]:
            self.d_wind_gust = self.h_wind_gust
        self.d_rain += self.h_rain
        self.d_valid = True
        self.reset_hourly()
        return retval
    def reset_daily(self):
        for i in range(16):
            self.d_wind_dir[i] = 0.0
        self.d_wind_acc = 0.0
        self.d_wind_count = 0
        self.d_wind_gust = (-1.0, None)
        self.d_rain = 0.0
        self.d_temp = {}
        for i in ('in', 'out'):
            self.d_temp[i] = Record()
            self.d_temp[i].ave = Average()
            self.d_temp[i].max = MaxTemp()
            self.d_temp[i].min = MinTemp()
        self.d_valid = False
    def get_daily(self):
        if not self.d_valid:
            self.reset_daily()
            return None
        retval = {}
        if self.d_wind_count > 0:
            best = 0
            for dir, val in self.d_wind_dir.items():
                if val > self.d_wind_dir[best]:
                    best = dir
            retval['wind_dir'] = best
            wind_ave = self.d_wind_acc / self.d_wind_count
            wind_ave = float(int(wind_ave * 100)) / 100.0
            retval['wind_ave'] = wind_ave
        else:
            retval['wind_dir'] = None
            retval['wind_ave'] = None
        if self.d_wind_gust[1]:
            retval['wind_gust'] = self.d_wind_gust[0]
        else:
            retval['wind_gust'] = None
        retval['wind_gust_t'] = self.d_wind_gust[1]
        retval['rain'] = self.d_rain
        for i in ('in', 'out'):
            retval['temp_%s_ave' % i] = self.d_temp[i].ave.result()
            retval['temp_%s_max' % i], retval['temp_%s_max_t' % i] = (
                self.d_temp[i].max.result())
            retval['temp_%s_min' % i], retval['temp_%s_min_t' % i] = (
                self.d_temp[i].min.result())
        self.reset_daily()
        return retval
class MonthAcc:
    """Derive monthly summary data from daily data."""
    def __init__(self, start):
        self.m_start = start
        self.m_temp = {}
        for i in ('in', 'out'):
            self.m_temp[i] = Record()
            self.m_temp[i].ave = Average()
            self.m_temp[i].min_lo = MinTemp()
            self.m_temp[i].min_hi = MaxTemp()
            self.m_temp[i].min_ave = Average()
            self.m_temp[i].max_lo = MinTemp()
            self.m_temp[i].max_hi = MaxTemp()
            self.m_temp[i].max_ave = Average()
        self.m_rain = 0.0
        self.m_valid = False
    def add(self, daily):
        self.m_idx = daily['idx']
        for i in ('in', 'out'):
            temp = daily['temp_%s_ave' % i]
            if temp != None:
                self.m_temp[i].ave.add(temp)
            temp = daily['temp_%s_min' % i]
            if temp != None:
                self.m_temp[i].min_lo.add(temp, daily['temp_%s_min_t' % i])
                self.m_temp[i].min_hi.add(temp, daily['temp_%s_min_t' % i])
                self.m_temp[i].min_ave.add(temp)
            temp = daily['temp_%s_max' % i]
            if temp != None:
                self.m_temp[i].max_lo.add(temp, daily['temp_%s_max_t' % i])
                self.m_temp[i].max_hi.add(temp, daily['temp_%s_max_t' % i])
                self.m_temp[i].max_ave.add(temp)
        self.m_rain += daily['rain']
        self.m_valid = True
    def get_monthly(self):
        if not self.m_valid:
            return None
        result = {}
        result['idx'] = self.m_idx
        result['start'] = self.m_start
        result['rain'] = self.m_rain
        for i in ('in', 'out'):
            result['temp_%s_ave' % i] = self.m_temp[i].ave.result()
            result['temp_%s_min_ave' % i] = self.m_temp[i].min_ave.result()
            result['temp_%s_min_lo' % i], result['temp_%s_min_lo_t' % i] = (
                self.m_temp[i].min_lo.result())
            result['temp_%s_min_hi' % i], result['temp_%s_min_hi_t' % i] = (
                self.m_temp[i].min_hi.result())
            result['temp_%s_max_ave' % i] = self.m_temp[i].max_ave.result()
            result['temp_%s_max_lo' % i], result['temp_%s_max_lo_t' % i] = (
                self.m_temp[i].max_lo.result())
            result['temp_%s_max_hi' % i], result['temp_%s_max_hi_t' % i] = (
                self.m_temp[i].max_hi.result())
        return result
def Process(params, raw_data, hourly_data, daily_data, monthly_data, verbose=1):
    """Generate summaries from raw weather station data.

    Starts from the last hourly or daily summary (whichever is
    earlier) and continues to end of the raw data.

    The meteorological day end (typically 2100 or 0900 local time) is set
    in the preferences file "weather.ini". The default value is 2100
    (2200 during DST), following the historical convention for weather
    station readings.

    Atmospheric pressure is converted from absolute to relative, using
    the weather station's offset as recorded by LogData.py. The
    pressure trend (change over three hours) is also computed.
    """
    HOUR = timedelta(hours=1)
    HOURx3 = timedelta(hours=3)
    SECOND = timedelta(seconds=1)
    DAY = timedelta(hours=24)
    # get time of last record
    last_raw = raw_data.before(datetime.max)
    if last_raw == None:
        raise IOError('No data found. Check data directory parameter.')
    # get earlier of last daily or hourly, and start from there
    start = hourly_data.before(datetime.max)
    if start != None:
        start = daily_data.before(start + SECOND)
    if start == None:
        start = raw_data.after(datetime.min)
    # get local time's offset from UTC, without DST
    time_offset = Local.utcoffset(last_raw) - Local.dst(last_raw)
    # set daytime end hour, in UTC
    day_end_hour = params.get('fixed', 'day end hour', None)
    if day_end_hour:
        # move definition to 'config' section
        params.set('config', 'day end hour', day_end_hour)
        params._config.remove_option('fixed', 'day end hour')
    day_end_hour = eval(params.get('config', 'day end hour', '21'))
    day_end_hour = (day_end_hour - (time_offset.seconds / 3600)) % 24
    # round to start of this day
    if start.hour < day_end_hour:
        start = start - DAY
    start = start.replace(hour=day_end_hour, minute=0, second=0)
    # get start of monthly data to be updated
    month_start = monthly_data.before(datetime.max)
    if month_start != None:
        month_start = min(month_start, start)
    # delete any existing records after start, as they may be incomplete
    del hourly_data[start + SECOND:]
    del daily_data[start + SECOND:]
    # preload pressure history, and find last valid rain
    pressure_offset = eval(params.get('fixed', 'pressure offset'))
    pressure_history = deque()
    last_rain = None
    for raw in raw_data[start - HOURx3:start]:
        pressure_history.append((raw['idx'], raw['abs_pressure']))
        if raw['rain'] != None:
            last_rain = raw['rain']
    acc = Acc(time_offset, last_rain)
    # process the data in day chunks
    while start <= last_raw:
        if verbose > 0:
            print "day:", start.isoformat()
        day_start = start
        # process each hour
        for hour in range(24):
            if start > last_raw:
                break
            # process each data item in the hour
            stop = start + HOUR
            for raw in raw_data[start:stop]:
                pressure_history.append((raw['idx'], raw['abs_pressure']))
                acc.add(raw)
                prev = raw
            # get hourly result
            new_data = acc.get_hourly()
#            if new_data and prev['idx'] + timedelta(minutes=1+prev['delay']) >= stop:
            if new_data and prev['idx'].minute >= 9:
                # store summary of hour
                # copy some current readings
                for key in ['idx', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
                            'abs_pressure']:
                    new_data[key] = prev[key]
                # convert pressure from absolute to relative
                new_data['rel_pressure'] = \
                    new_data['abs_pressure'] + pressure_offset
                # compute pressure trend
                target = new_data['idx'] - HOURx3
                while len(pressure_history) >= 2 and \
                      abs(pressure_history[0][0] - target) > \
                      abs(pressure_history[1][0] - target):
                    pressure_history.popleft()
                if len(pressure_history) >= 1 and \
                   abs(pressure_history[0][0] - target) < \
                   timedelta(minutes=prev['delay']):
                    new_data['pressure_trend'] = new_data['abs_pressure'] - \
                                                 pressure_history[0][1]
                else:
                    new_data['pressure_trend'] = None
                # store new hourly data
                hourly_data[new_data['idx']] = new_data
            start = stop
        # store summary of day
        new_data = acc.get_daily()
        if new_data:
            new_data['idx'] = min(stop, last_raw)
            new_data['start'] = day_start
            daily_data[new_data['idx']] = new_data
    # compute monthly data from daily data
    start = month_start
    if start == None:
        start = daily_data.after(datetime.min)
    # set start to end of first day of month
    if start.hour < day_end_hour:
        start = start - DAY
    start = start.replace(day=1, hour=day_end_hour, minute=0, second=0)
    # calculate offset to just after start of day
    month_offset = timedelta(hours=23, minutes=55)
    # adjust offset for extreme time zones / day end hours
    local_start = start + time_offset
    if local_start.day == 2:
        if local_start.hour >= 12:
            # missing most of first day of month
            month_offset = month_offset + DAY
    elif local_start.day != 1 or local_start.hour < 12:
        # most or all of day is in last month
        month_offset = month_offset - DAY
    # get start of actual data to be processed
    t0 = start - month_offset
    # delete any existing records after start, as they may be incomplete
    del monthly_data[t0:]
    # process data
    while t0 <= last_raw:
        if start.month < 12:
            stop = start.replace(month=start.month+1)
        else:
            stop = start.replace(year=start.year+1, month=1)
        # get month limits
        t1 = stop - month_offset
        if verbose > 0:
            print "month:", start.isoformat()
        acc = MonthAcc(daily_data[daily_data.after(t0)]['start'])
        for data in daily_data[t0:t1]:
            acc.add(data)
        new_data = acc.get_monthly()
        if new_data:
            monthly_data[new_data['idx']] = new_data
        start = stop
        t0 = t1
    return 0
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    for o, a in opts:
        if o == '--help':
            print __doc__.strip()
            return 0
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    data_dir = args[0]
    return Process(DataStore.params(data_dir),
                   DataStore.data_store(data_dir),
                   DataStore.hourly_store(data_dir),
                   DataStore.daily_store(data_dir),
                   DataStore.monthly_store(data_dir))
if __name__ == "__main__":
    sys.exit(main())
