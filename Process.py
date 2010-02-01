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
        temp_out = raw['temp_out']
        if temp_out != None:
            self.d_temp_acc += temp_out
            self.d_temp_count += 1
            if self._daytime[idx.hour]:
                # daytime max temperature
                if temp_out > self.d_temp_max[0]:
                    self.d_temp_max = (temp_out, idx)
            else:
                # nightime min temperature
                if temp_out <= self.d_temp_min[0]:
                    self.d_temp_min = (temp_out, idx)
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
        self.d_temp_acc = 0.0
        self.d_temp_count = 0
        self.d_temp_max = (-1000.0, None)
        self.d_temp_min = (1000.0, None)
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
        if self.d_temp_count > 0:
            retval['temp_out_ave'] = self.d_temp_acc / float(self.d_temp_count)
        else:
            retval['temp_out_ave'] = None
        if self.d_temp_max[1]:
            retval['temp_out_max'] = self.d_temp_max[0]
        else:
            retval['temp_out_max'] = None
        retval['temp_out_max_t'] = self.d_temp_max[1]
        if self.d_temp_min[1]:
            retval['temp_out_min'] = self.d_temp_min[0]
        else:
            retval['temp_out_min'] = None
        retval['temp_out_min_t'] = self.d_temp_min[1]
        self.reset_daily()
        return retval
class MonthAcc:
    """Derive monthly summary data from daily data."""
    def __init__(self, start):
        self.m_start = start
        self.m_temp_acc = 0.0
        self.m_temp_count = 0
        self.m_temp_out_min_lo = (1000.0, None)
        self.m_temp_out_min_hi = (-1000.0, None)
        self.m_temp_out_min_acc = 0.0
        self.m_temp_out_max_lo = (1000.0, None)
        self.m_temp_out_max_hi = (-1000.0, None)
        self.m_temp_out_max_acc = 0.0
        self.m_rain = 0.0
        self.m_min_count = 0
        self.m_max_count = 0
        self.m_valid = False
    def add(self, daily):
        self.m_idx = daily['idx']
        temp_out_ave = daily['temp_out_ave']
        if temp_out_ave != None:
            self.m_temp_acc += temp_out_ave
            self.m_temp_count += 1
        temp_out_min = daily['temp_out_min']
        if temp_out_min != None:
            if self.m_temp_out_min_lo[0] > temp_out_min:
                self.m_temp_out_min_lo = (temp_out_min, daily['temp_out_min_t'])
            if self.m_temp_out_min_hi[0] < temp_out_min:
                self.m_temp_out_min_hi = (temp_out_min, daily['temp_out_min_t'])
            self.m_temp_out_min_acc += temp_out_min
            self.m_min_count += 1
        temp_out_max = daily['temp_out_max']
        if temp_out_max != None:
            if self.m_temp_out_max_lo[0] > temp_out_max:
                self.m_temp_out_max_lo = (temp_out_max, daily['temp_out_max_t'])
            if self.m_temp_out_max_hi[0] < temp_out_max:
                self.m_temp_out_max_hi = (temp_out_max, daily['temp_out_max_t'])
            self.m_temp_out_max_acc += temp_out_max
            self.m_max_count += 1
        self.m_rain += daily['rain']
        self.m_valid = True
    def get_monthly(self):
        if not self.m_valid:
            return None
        result = {}
        result['idx'] = self.m_idx
        result['start'] = self.m_start
        if self.m_temp_count > 0:
            result['temp_out_ave'] = self.m_temp_acc / float(self.m_temp_count)
        else:
            result['temp_out_ave'] = None
        if self.m_temp_out_min_lo[1]:
            result['temp_out_min_lo'] = self.m_temp_out_min_lo[0]
        else:
            result['temp_out_min_lo'] = None
        result['temp_out_min_lo_t'] = self.m_temp_out_min_lo[1]
        if self.m_temp_out_min_hi[1]:
            result['temp_out_min_hi'] = self.m_temp_out_min_hi[0]
        else:
            result['temp_out_min_hi'] = None
        result['temp_out_min_hi_t'] = self.m_temp_out_min_hi[1]
        result['temp_out_min_ave'] = self.m_temp_out_min_acc
        if self.m_temp_out_max_lo[1]:
            result['temp_out_max_lo'] = self.m_temp_out_max_lo[0]
        else:
            result['temp_out_max_lo'] = None
        result['temp_out_max_lo_t'] = self.m_temp_out_max_lo[1]
        if self.m_temp_out_max_hi[1]:
            result['temp_out_max_hi'] = self.m_temp_out_max_hi[0]
        else:
            result['temp_out_max_hi'] = None
        result['temp_out_max_hi_t'] = self.m_temp_out_max_hi[1]
        result['temp_out_max_ave'] = self.m_temp_out_max_acc
        result['rain'] = self.m_rain
        if self.m_min_count > 0:
            result['temp_out_min_ave'] = (
                self.m_temp_out_min_acc / float(self.m_min_count))
        else:
            result['temp_out_min_ave'] = None
        if self.m_max_count > 0:
            result['temp_out_max_ave'] = (
                self.m_temp_out_max_acc / float(self.m_max_count))
        else:
            result['temp_out_max_ave'] = None
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
    pressure_offset = eval(params.get('fixed', 'pressure offset'))
    # get time of last record
    last_raw = raw_data.before(datetime.max)
    # get earlier of last daily or hourly, and start from there
    start = hourly_data.before(datetime.max)
    if start != None:
        start = daily_data.before(start + SECOND)
    if start == None:
        start = raw_data.after(datetime.min)
    # get local time's offset from UTC, without DST
    time_offset = Local.utcoffset(last_raw) - Local.dst(last_raw)
    # set daytime end hour, in UTC
    day_end_hour = eval(params.get('fixed', 'day end hour', '21'))
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
