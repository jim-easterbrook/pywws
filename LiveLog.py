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
from pywws.Logger import ApplicationLogger
from pywws import Process
from pywws import Tasks
from pywws import ToUnderground
from pywws import WeatherStation

def CheckFixedBlock(ws, params, logger):
    fixed_block = ws.get_fixed_block(unbuffered=True)
    if not fixed_block:
        return None
    # check clocks
    s_time = DataStore.safestrptime(fixed_block['date_time'], '%Y-%m-%d %H:%M')
    c_time = datetime.now().replace(second=0, microsecond=0)
    diff = abs(s_time - c_time)
    if diff > timedelta(minutes=2):
        logger.warning(
            "Computer and weather station clocks disagree by %s (H:M:S).", str(diff))
    # store info from fixed block
    pressure_offset = fixed_block['rel_pressure'] - fixed_block['abs_pressure']
    old_offset = eval(params.get('fixed', 'pressure offset', 'None'))
    if old_offset and abs(old_offset - pressure_offset) > 0.01:
        # re-read fixed block, as can get incorrect values
        logger.warning('Re-read fixed block')
        fixed_block = ws.get_fixed_block(unbuffered=True)
        if not fixed_block:
            return None
        pressure_offset = fixed_block['rel_pressure'] - fixed_block['abs_pressure']
    if old_offset and abs(old_offset - pressure_offset) > 0.01:
        logger.warning(
            'Pressure offset change: %g -> %g', old_offset, pressure_offset)
    params.set('fixed', 'pressure offset', '%g' % (pressure_offset))
    params.flush()
    return fixed_block
def LiveLog(data_dir):
    logger = logging.getLogger('pywws.LiveLog')
    params = DataStore.params(data_dir)
    # connect to weather station
    ws = WeatherStation.weather_station()
    fixed_block = CheckFixedBlock(ws, params, logger)
    if not fixed_block:
        logger.error("Invalid data from weather station")
        return 3
    # open data file stores
    raw_data = DataStore.data_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    # create a translation object for our locale
    translation = Localisation.GetTranslation(params)
    # create a ToUnderground object
    underground = ToUnderground.ToUnderground(params, raw_data)
    # create a RegularTasks object
    tasks = Tasks.RegularTasks(
        params, raw_data, hourly_data, daily_data, monthly_data, translation)
    # get time of last logged data
    two_minutes = timedelta(minutes=2)
    last_stored = raw_data.before(datetime.max)
    if last_stored == None:
        last_stored = datetime.min
    if datetime.utcnow() < last_stored:
        logger.error('Computer time is earlier than last stored data')
        return 4
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
            last_date = now - timedelta(minutes=data['delay'])
            if last_date > last_stored:
                last_ptr = ws.dec_ptr(ptr)
                fixed_block = ws.get_fixed_block(unbuffered=True)
                max_count = min(fixed_block['data_count'], 4079)
                while last_date > last_stored and count < max_count:
                    data = ws.get_data(last_ptr)
                    raw_data[last_date] = data
                    count += 1
                    last_date -= timedelta(minutes=data['delay'])
                    last_ptr = ws.dec_ptr(last_ptr)
            last_stored = now + two_minutes
            if count > 1:
                logger.info("%d records written", count)
            # process new data
            raw_data.flush()
            Process.Process(
                params, raw_data, hourly_data, daily_data, monthly_data)
            # do tasks
            tasks.do_tasks()
            if now >= next_hour:
                next_hour += hour
                fixed_block = CheckFixedBlock(ws, params, logger)
                if not fixed_block:
                    logger.error("Invalid data from weather station")
                    return 3
            params.flush()
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
    logger = logging.getLogger('pywws')
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
    except Exception, e:
        logger.exception(str(e))
