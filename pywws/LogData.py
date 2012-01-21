#!/usr/bin/env python

"""
Save weather station history to file.

usage: python LogData.py [options] data_dir
options are:
  -h   | --help     display this help
  -c   | --clear    clear weather station's memory full indicator
  -s n | --sync n   set quality of synchronisation to weather station (0 or 1)
  -v   | --verbose  increase number of informative messages
data_dir is the root directory of the weather data
"""

from datetime import datetime, timedelta
import getopt
import logging
import os
import sys
import time

import DataStore
from Logger import ApplicationLogger
from TimeZone import Local
import WeatherStation

def LogData(params, raw_data, sync=None, clear=False):
    logger = logging.getLogger('pywws.LogData')
    # connect to weather station
    ws_type = params.get('config', 'ws type', '1080')
    ws = WeatherStation.weather_station(ws_type=ws_type)
    fixed_block = ws.get_fixed_block()
    if not fixed_block:
        logger.error("Invalid data from weather station")
        return 3
    # get sync config value
    if sync is None:
        sync = int(params.get('config', 'logdata sync', '1'))
    # get time to go back to
    last_stored = raw_data.before(datetime.max)
    if last_stored == None:
        last_stored = datetime.min
    if datetime.utcnow() < last_stored:
        logger.error('Computer time is earlier than last stored data')
        return 4
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
        logger.warning(
            'Pressure offset change: %g -> %g', old_offset, pressure_offset)
    params.set('fixed', 'pressure offset', '%g' % (pressure_offset))
    params.flush()
    # get address and date-time of last complete logged data
    logger.info('Synchronising to weather station')
    for data, last_ptr, logged in ws.live_data():
        last_date = data['idx']
        logger.debug('Reading time %s', last_date.strftime('%H:%M:%S'))
        if logged:
            fixed_block = ws.get_fixed_block(unbuffered=True)
            break
        if sync < 1 and last_date.second > 5 and last_date.second < 55:
            last_date = last_date.replace(second=0) - timedelta(minutes=data['delay'])
            last_ptr = ws.dec_ptr(last_ptr)
            break
    # go back through stored data, until we catch up with what we've already got
    logger.info('Fetching data')
    last_stored += timedelta(minutes=fixed_block['read_period'] / 2)
    count = 0
    # data_count includes record currently being updated every 48 seconds
    max_count = fixed_block['data_count'] - 1
    while last_date > last_stored and count < max_count:
        data = ws.get_data(last_ptr)
        if data['delay'] is None or data['delay'] > 30:
            logger.error('invalid data at %04x, %s',
                         last_ptr, last_date.isoformat(' '))
            last_date -= timedelta(minutes=fixed_block['read_period'])
        else:
            raw_data[last_date] = data
            count += 1
            last_date -= timedelta(minutes=data['delay'])
        last_ptr = ws.dec_ptr(last_ptr)
    logger.info("%d records written", count)
    raw_data.flush()
    if clear:
        logger.info('Clearing weather station memory')
        ptr = ws.fixed_format['data_count'][0]
        ws.write_data([(ptr, 1), (ptr+1, 0)])
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(
            argv[1:], "hcs:v", ('help', 'clear', 'sync=', 'verbose'))
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    clear = False
    sync = None
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print __doc__.strip()
            return 0
        elif o in ('-c', '--clear'):
            clear = True
        elif o in ('-s', '--sync'):
            sync = int(a)
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, 'Error: 1 argument required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    root_dir = args[0]
    return LogData(
        DataStore.params(root_dir), DataStore.data_store(root_dir),
        sync=sync, clear=clear)
if __name__ == "__main__":
    sys.exit(main())
