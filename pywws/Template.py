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

"""Create text data file based on a template
::

%s

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.Template [options] data_dir template_file output_file
 options are:
  --help    display this help
 data_dir is the root directory of the weather data
 template_file is the template text source file
 output_file is the name of the text file to be created
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import codecs
from datetime import datetime, timedelta
import getopt
import locale
import logging
import os
import shlex
import sys

from pywws.conversions import *
from pywws import DataStore
from pywws.Forecast import Zambretti, ZambrettiCode
from pywws import Localisation
from pywws.Logger import ApplicationLogger
from pywws.TimeZone import Local, utc
from pywws import WeatherStation

SECOND = timedelta(seconds=1)
HOUR = timedelta(hours=1)
DAY = timedelta(hours=24)

class Template(object):
    def __init__(self, params, calib_data, hourly_data, daily_data, monthly_data,
                 use_locale=True):
        self.logger = logging.getLogger('pywws.Template')
        self.params = params
        self.calib_data = calib_data
        self.hourly_data = hourly_data
        self.daily_data = daily_data
        self.monthly_data = monthly_data
        self.use_locale = use_locale
        self.midnight = None
        self.rain_midnight = None
        # get character encoding of template input & output
        self.encoding = params.get('config', 'template encoding', 'iso-8859-1')
        self.local_data = {
            'altitude': self.get_option('altitude', cast_type=int),
            'latitude': self.get_option('latitude', cast_type=float),
            'longitude': self.get_option('longitude', cast_type=float)
        }

    def get_option(self, option, default=None, cast_type=None):
        if self.params.has_option('config', option):
            val = self.params.get('config', option, default)
            return cast_type(val) if cast_type else val

        return None

    def process(self, live_data, template_file):
        def jump(idx, count):
            while count > 0:
                new_idx = data_set.after(idx + SECOND)
                if new_idx == None:
                    break
                idx = new_idx
                count -= 1
            while count < 0:
                new_idx = data_set.before(idx)
                if new_idx == None:
                    break
                idx = new_idx
                count += 1
            return idx, count == 0

        def location_is_set():
            return self.local_data['latitude'] and self.local_data['longitude']

        params = self.params
        if not live_data:
            idx = self.calib_data.before(datetime.max)
            if not idx:
                self.logger.error("No calib data - run Process.py first")
                return
            live_data = self.calib_data[idx]
        pressure_trend_text = WeatherStation.pressure_trend_text
        wind_dir_text = WeatherStation.get_wind_dir_text()
        dew_point = WeatherStation.dew_point
        wind_chill = WeatherStation.wind_chill
        apparent_temp = WeatherStation.apparent_temp
        rain_hour = self._rain_hour
        rain_day = self._rain_day
        rain_24 = self._rain_24
        get_option = self.get_option
        pressure_offset = eval(self.params.get('fixed', 'pressure offset'))
        fixed_block = eval(self.params.get('fixed', 'fixed block'))
        # start off with no time rounding
        round_time = None
        # start off in hourly data mode
        data_set = self.hourly_data
        # start off in utc
        time_zone = utc
        # jump to last item
        idx, valid_data = jump(datetime.max, -1)
        if not valid_data:
            self.logger.error("No summary data - run Process.py first")
            return
        data = data_set[idx]
        local_data = self.local_data
        # open template file file
        if sys.version_info[0] >= 3:
            tmplt = open(template_file, 'r', encoding=self.encoding)
        else:
            tmplt = open(template_file, 'r')
        # do the text processing
        while True:
            line = tmplt.readline()
            if line == '':
                break
            parts = line.split('#')
            for i in range(len(parts)):
                if i % 2 == 0:
                    # not a processing directive
                    if i == 0 or parts[i] != '\n':
                        yield parts[i]
                    continue
                if parts[i] and parts[i][0] == '!':
                    # comment
                    continue
                command = shlex.split(parts[i])
                if command == []:
                    # empty command == print a single '#'
                    yield '#'
                elif command[0] in (data.keys() + self.local_data.keys() + ['calc']):
                    # output a value
                    if not valid_data:
                        continue
                    # format is: key fmt_string no_value_string conversion
                    # get value
                    if command[0] == 'calc':
                        x = eval(command[1])
                        del command[1]
                    else:
                        if command[0] in local_data.keys():
                            x = self.local_data[command[0]]
                        else:
                            x = data[command[0]]
                    # adjust time
                    if isinstance(x, datetime):
                        if round_time:
                            x += round_time
                        x = x.replace(tzinfo=utc)
                        x = x.astimezone(time_zone)
                    # convert data
                    if x != None and len(command) > 3:
                        x = eval(command[3])
                    # get format
                    fmt = '%s'
                    if len(command) > 1:
                        fmt = command[1]
                    # write output
                    if x == None:
                        if len(command) > 2:
                            yield command[2]
                    elif isinstance(x, datetime):
                        yield x.strftime(fmt)
                    elif not self.use_locale:
                        yield fmt % (x)
                    elif sys.version_info >= (2, 7) or '%%' not in fmt:
                        yield locale.format_string(fmt, x)
                    else:
                        yield locale.format_string(
                            fmt.replace('%%', '##'), x).replace('##', '%')
                elif command[0] == 'monthly':
                    data_set = self.monthly_data
                    idx, valid_data = jump(datetime.max, -1)
                    data = data_set[idx]
                elif command[0] == 'daily':
                    data_set = self.daily_data
                    idx, valid_data = jump(datetime.max, -1)
                    data = data_set[idx]
                elif command[0] == 'hourly':
                    data_set = self.hourly_data
                    idx, valid_data = jump(datetime.max, -1)
                    data = data_set[idx]
                elif command[0] == 'raw':
                    data_set = self.calib_data
                    idx, valid_data = jump(datetime.max, -1)
                    data = data_set[idx]
                elif command[0] == 'live':
                    data_set = self.calib_data
                    idx = datetime.max
                    valid_data = True
                    data = live_data
                elif command[0] == 'timezone':
                    if command[1] == 'utc':
                        time_zone = utc
                    elif command[1] == 'local':
                        time_zone = Local
                    else:
                        self.logger.error("Unknown time zone: %s", command[1])
                        return
                elif command[0] == 'roundtime':
                    if eval(command[1]):
                        round_time = timedelta(seconds=30)
                    else:
                        round_time = None
                elif command[0] == 'jump':
                    prevdata = data
                    idx, valid_data = jump(idx, int(command[1]))
                    data = data_set[idx]
                elif command[0] == 'goto':
                    prevdata = data
                    time_str = command[1]
                    if '%' in time_str:
                        lcl = idx.replace(tzinfo=utc).astimezone(time_zone)
                        time_str = lcl.strftime(time_str)
                    new_idx = DataStore.safestrptime(time_str)
                    new_idx = new_idx.replace(tzinfo=time_zone).astimezone(utc)
                    new_idx = data_set.after(new_idx.replace(tzinfo=None))
                    if new_idx:
                        idx = new_idx
                        data = data_set[idx]
                        valid_data = True
                    else:
                        valid_data = False
                elif command[0] == 'loop':
                    loop_count = int(command[1])
                    loop_start = tmplt.tell()
                elif command[0] == 'endloop':
                    loop_count -= 1
                    if valid_data and loop_count > 0:
                        tmplt.seek(loop_start, 0)
                else:
                    self.logger.error(
                        "Unknown processing directive: #%s#", parts[i])
                    return
        tmplt.close()
        return

    def make_text(self, template_file, live_data=None):
        result = ''
        for text in self.process(live_data, template_file):
            if sys.version_info[0] < 3 and isinstance(text, unicode):
                text = text.encode(self.encoding)
            result += text
        return result

    def make_file(self, template_file, output_file, live_data=None):
        if sys.version_info[0] >= 3:
            of = open(output_file, 'w', encoding=self.encoding)
        else:
            of = open(output_file, 'w')
        for text in self.process(live_data, template_file):
            if sys.version_info[0] < 3 and isinstance(text, unicode):
                text = text.encode(self.encoding)
            of.write(text)
        of.close()
        return 0

    def _rain_hour(self, data):
        rain_hour = self.calib_data[self.calib_data.nearest(data['idx'] - HOUR)]['rain']
        return max(0.0, data['rain'] - rain_hour)

    def _rain_24(self, data):
        rain_24 = self.calib_data[self.calib_data.nearest(data['idx'] - DAY)]['rain']
        return max(0.0, data['rain'] - rain_24)

    def _rain_day(self, data):
        if not self.midnight:
            self.midnight = datetime.utcnow().replace(tzinfo=utc).astimezone(
                Local).replace(hour=0, minute=0, second=0).astimezone(
                    utc).replace(tzinfo=None)
        while data['idx'] < self.midnight:
            self.midnight -= DAY
            self.rain_midnight = None
        while data['idx'] >= self.midnight + DAY:
            self.midnight += DAY
            self.rain_midnight = None
        if self.rain_midnight is None:
            self.rain_midnight = self.calib_data[
                self.calib_data.nearest(self.midnight)]['rain']
        return max(0.0, data['rain'] - self.rain_midnight)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # check arguments
    if len(args) != 3:
        print >>sys.stderr, 'Error: 3 arguments required\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    # process options
    for o, a in opts:
        if o == '--help':
            print __usage__.strip()
            return 0
    logger = ApplicationLogger(1)
    params = DataStore.params(args[0])
    Localisation.SetApplicationLanguage(params)
    return Template(
        params,
        DataStore.calib_store(args[0]), DataStore.hourly_store(args[0]),
        DataStore.daily_store(args[0]), DataStore.monthly_store(args[0])
        ).make_file(args[1], args[2])

if __name__ == "__main__":
    sys.exit(main())
