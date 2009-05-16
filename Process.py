#!/usr/bin/env python
"""
Generate hourly and daily summaries of raw weather station data.

usage: python Process.py [options] data_dir
options are:
\t--help\t\tdisplay this help
data_dir is the root directory of the weather data
"""

from collections import defaultdict, deque
from datetime import date, datetime, timedelta
import getopt
import os
import sys

import DataStore
from TimeZone import Local, utc
import WeatherStation

class Acc:
    """'Accumulate' raw weather data to produce a summary.

    Compute average wind speed, log maximum wind gust, find dominant
    wind direction and compute total rainfall."""

    def __init__(self):
        self.wind_ave = 0.0
        self.wind_gust = (0.0, None)
        self.wind_dir = defaultdict(float)
        self.rain = 0.0
        self.count = 0
        self.valid = False
    def add(self, raw, last_raw):
        """Add a raw data reading.

        last_raw is used to get the rainfall in this period."""
        if raw['wind_ave'] != None:
            if raw['wind_dir'] != None:
                self.wind_dir[raw['wind_dir']] += raw['wind_ave']
            self.wind_ave += raw['wind_ave']
            self.count += 1
        if raw['wind_gust'] != None:
            if raw['wind_gust'] > self.wind_gust[0]:
                self.wind_gust = (raw['wind_gust'], raw['idx'])
        if raw['rain'] < last_raw['rain'] - 0.001:
            print '%s rain reset %.1f -> %.1f' % (
                raw['idx'], last_raw['rain'], raw['rain'])
        else:
            self.rain += raw['rain'] - last_raw['rain']
        self.valid = True
    def result(self):
        """Get the result of the data accumulation."""
        retval = {}
        if self.count > 0:
            self.wind_ave = self.wind_ave / self.count
            self.wind_ave = float(int(self.wind_ave * 100)) / 100.0
            retval['wind_ave'] = self.wind_ave
            retval['wind_gust_t'] = self.wind_gust[1]
            retval['wind_gust'] = self.wind_gust[0]
            best = self.wind_dir.keys()[0]
            for dir, val in self.wind_dir.items():
                if val > self.wind_dir[best]:
                    best = dir
            retval['wind_dir'] = best
        else:
            retval['wind_ave'] = None
            retval['wind_gust_t'] = None
            retval['wind_gust'] = None
            retval['wind_dir'] = None
        retval['rain'] = self.rain
        return retval
class Hour_Acc(Acc):
    def result(self, raw):
        retval = Acc.result(self)
        del retval['wind_gust_t']
        for key in ['idx', 'hum_in', 'temp_in', 'hum_out', 'temp_out',
                    'abs_pressure']:
            retval[key] = raw[key]
        return retval
class Day_Acc(Acc):
    """Similar to Acc(), but also logs daytime max and nighttime min
    temperatures.

    Daytime is assumed to be 0900-2100 and nighttime to be 2100-0900,
    local time (1000-2200 and 2200-1000 during DST)."""
    def __init__(self, day_end_hour):
        Acc.__init__(self)
        self._day_end_hour = day_end_hour
        self.temp_out_min = (1000.0, None)
        self.temp_out_max = (-1000.0, None)
    def add(self, raw, last_raw):
        if raw['temp_out'] != None:
            if raw['idx'].hour >= (self._day_end_hour + 12) % 24 and \
               raw['idx'].hour < self._day_end_hour:
                # daytime max temperature
                if raw['temp_out'] > self.temp_out_max[0]:
                    self.temp_out_max = (raw['temp_out'], raw['idx'])
            else:
                # nightime min temperature
                if raw['temp_out'] <= self.temp_out_min[0]:
                    self.temp_out_min = (raw['temp_out'], raw['idx'])
        Acc.add(self, raw, last_raw)
    def result(self):
        retval = Acc.result(self)
        if self.temp_out_min[1] != None:
            retval['temp_out_min'] = self.temp_out_min[0]
        else:
            retval['temp_out_min'] = None
        retval['temp_out_min_t'] = self.temp_out_min[1]
        if self.temp_out_max[1] != None:
            retval['temp_out_max'] = self.temp_out_max[0]
        else:
            retval['temp_out_max'] = None
        retval['temp_out_max_t'] = self.temp_out_max[1]
        return retval
def Process(params, raw_data, hourly_data, daily_data):
    """Generate hourly and daily summaries from raw weather station
    data.

    Starts from the last hourly or daily summary (whichever is
    earlier) and continues to end of the raw data.

    A day is assumed to end at 2100 local time (2200 during DST),
    following the historical convention for weather station readings.

    Atmospheric pressure is converted from absolute to relative, using
    the weather station's offset as recorded by LogData.py. The
    pressure trend (change over three hours) is also computed.
    """
    HOUR = timedelta(hours=1)
    HOURx3 = timedelta(hours=3)
    pressure_offset = eval(params.get('fixed', 'pressure offset'))
    # get time of last existing records
    last_raw = raw_data.before(datetime.max)
    last_hour = hourly_data.before(datetime.max)
    last_day = daily_data.before(datetime.max)
    # get earlier of last daily or hourly, and start from there
    if last_day == None or last_hour == None:
        start = raw_data.after(datetime.min)
    elif last_hour < last_day:
        start = raw_data.after(last_hour)
    else:
        start = raw_data.after(last_day)
    # get local time's offset from UTC, without DST
    time_offset = Local.utcoffset(last_raw) - Local.dst(last_raw)
    # set daytime end hour, in UTC
    day_end_hour = (21 - (time_offset.seconds / 3600)) % 24
    # round to start of this day
    if start.hour < day_end_hour:
        start = start - timedelta(hours=24)
    start = start.replace(hour=day_end_hour, minute=0, second=0)
    # delete any existing records after start, as they may be incomplete
    while last_hour != None and hourly_data[last_hour]['idx'] > start:
        del hourly_data[last_hour]
        last_hour = hourly_data.before(datetime.max)
    while last_day != None and daily_data[last_day]['idx'] > start:
        del daily_data[last_day]
        last_day = daily_data.before(datetime.max)
    # preload pressure history
    pressure_history = deque()
    for raw in raw_data[start - HOURx3:start]:
        pressure_history.append((raw['idx'], raw['abs_pressure']))
    # get last raw data before we start
    prev = raw_data.before(start)
    if prev == None:
        prev = raw_data.after(start)
    prev = raw_data[prev]
    # process the data in day chunks
    while start <= last_raw:
        print start.isoformat()
        day_start = start
        day_acc = Day_Acc(day_end_hour)
        # process each hour
        for hour in range(24):
            hour_acc = Hour_Acc()
            # process each data item in the hour
            stop = start + HOUR
            for raw in raw_data[start:stop]:
                pressure_history.append((raw['idx'], raw['abs_pressure']))
                hour_acc.add(raw, prev)
                day_acc.add(raw, prev)
                prev = raw
            if hour_acc.valid and \
               prev['idx'] + timedelta(minutes=1+prev['delay']) >= stop:
                # store summary of hour
                new_data = hour_acc.result(prev)
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
                # convert pressure from absolute to relative
                new_data['rel_pressure'] = \
                    new_data['abs_pressure'] + pressure_offset
                hourly_data[new_data['idx']] = new_data
            start = stop
        if day_acc.valid:
            # store summary of day
            new_data = day_acc.result()
            new_data['idx'] = min(stop, last_raw)
            new_data['start'] = day_start
            daily_data[new_data['idx']] = new_data
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
                   DataStore.daily_store(data_dir))
if __name__ == "__main__":
    sys.exit(main())
