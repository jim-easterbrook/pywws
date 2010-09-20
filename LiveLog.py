#!/usr/bin/env python

"""Get weather data, store it, and process it.

Run this continuously, having set what tasks are to be done.

usage: python LiveLog.py [options] data_dir
options are:
  -h      or --help      display this help
  -l file or --log file  write log information to file
  -v      or --verbose   increase amount of reassuring messages
data_dir is the root directory of the weather data (e.g. /data/weather)
"""

from datetime import datetime, timedelta
import getopt
import logging
import os
import sys
import time

from pywws import DataStore
from pywws import Localisation
from pywws import LogData
from pywws.Logger import ApplicationLogger
from pywws import Process
from pywws import Tasks
from pywws.TimeZone import Local, utc
from pywws import ToUnderground
from pywws import Upload
from pywws import WeatherStation

def LiveLog(data_dir):
    logger = logging.getLogger('pywws.LiveLog')
    params = DataStore.params(data_dir)
    # open data file stores
    raw_data = DataStore.data_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    # create a translation object for our locale
    translation = Localisation.GetTranslation(params)
    # create a ToUnderground object
    underground = ToUnderground.ToUnderground(params, raw_data)
    # get local time's offset from UTC, without DST
    now = datetime.utcnow()
    time_offset = Local.utcoffset(now) - Local.dst(now)
    # get daytime end hour, in UTC
    day_end_hour = eval(params.get('config', 'day end hour', '21'))
    day_end_hour = (day_end_hour - (time_offset.seconds / 3600)) % 24
    # connect to weather station
    ws = WeatherStation.weather_station()
    fixed_block = ws.get_fixed_block()
    # get time of last logged data
    two_minutes = timedelta(minutes=2)
    last_stored = raw_data.before(datetime.max)
    if last_stored == None:
        last_stored = datetime.min
    last_stored += two_minutes
    # get live data
    hour = timedelta(hours=1)
    next_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + hour
    for data, ptr, logged in ws.live_data():
        now = data['idx']
        if logged:
            # store logged data
            raw_data[now] = data
            count = 1
            # catchup any missing data
            last_ptr = ptr
            last_date = now
            while count < fixed_block['data_count'] - 1:
                last_ptr = ws.dec_ptr(last_ptr)
                last_date -= timedelta(minutes=data['delay'])
                if last_date <= last_stored:
                    break
                data = ws.get_data(last_ptr)
                raw_data[last_date] = data
                count += 1
            last_stored = now + two_minutes
            if count > 1:
                logger.info("%d records written", count)
            # process new data
            raw_data.flush()
            Process.Process(
                params, raw_data, hourly_data, daily_data, monthly_data)
            # do tasks
            sections = ['live']
            if now >= next_hour:
                next_hour += hour
                sections.append('hourly')
                if (now.hour - day_end_hour) % 12 == 0:
                    sections.append('12 hourly')
                if (now.hour - day_end_hour) % 24 == 0:
                    sections.append('daily')
            uploads = []
            for section in sections:
                Tasks.DoTwitter(
                    section, params, raw_data, hourly_data, daily_data, monthly_data,
                    translation)
                if eval(params.get(section, 'underground', 'False')):
                    underground.Upload(True)
                uploads += Tasks.DoPlots(
                    section, params, raw_data, hourly_data, daily_data, monthly_data,
                    translation)
                uploads += Tasks.DoTemplates(
                    section, params, raw_data, hourly_data, daily_data, monthly_data,
                    translation)
            if uploads:
                Upload.Upload(params, uploads)
            for file in uploads:
                os.unlink(file)
        elif eval(params.get('live', 'underground', 'False')):
            underground.RapidFire(data, True)
    return 0
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hl:v", ['help', 'log=', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    logfile = None
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print __doc__.strip()
            return 0
        elif o in ('-l', '--log'):
            logfile = a
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    logger = ApplicationLogger(verbose, logfile)
    return LiveLog(args[0])
if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
