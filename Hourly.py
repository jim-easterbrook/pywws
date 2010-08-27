#!/usr/bin/env python

"""Get weather data, process it, prepare graphs & text files and
upload to a web site.

Typically run every hour from cron.
Comment out or remove the bits you don't need.

usage: python Hourly.py [options] [data_dir]
options are:
\t-h or --help\t\tdisplay this help
\t-v or --verbose\t\tincrease amount of reassuring messages
data_dir is the root directory of the weather data (default /data/weather)
"""

from datetime import datetime, timedelta
import getopt
import os
import sys

from pywws import DataStore
from pywws import Localisation
from pywws import LogData
from pywws.Logger import ApplicationLogger
from pywws import Process
from pywws import Tasks
from pywws.TimeZone import Local, utc
from pywws import Upload

def Hourly(data_dir):
    # get file locations
    params = DataStore.params(data_dir)
    # open data file stores
    raw_data = DataStore.data_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    # create a translation object for our locale
    translation = Localisation.GetTranslation(params)
    # get weather station data
    LogData.LogData(params, raw_data)
    # do the processing
    Process.Process(params, raw_data, hourly_data, daily_data, monthly_data)
    # get local time's offset from UTC, without DST
    last_raw = raw_data.before(datetime.max)
    time_offset = Local.utcoffset(last_raw) - Local.dst(last_raw)
    # get daytime end hour, in UTC
    day_end_hour = eval(params.get('config', 'day end hour', '21'))
    day_end_hour = (day_end_hour - (time_offset.seconds / 3600)) % 24
    # get hours since day end hour
    hour = (last_raw + timedelta(minutes=raw_data[last_raw]['delay'])).hour
    hour -= day_end_hour
    sections = ['hourly']
    if hour % 12 == 0:
        sections.append('12 hourly')
    if hour % 24 == 0:
        sections.append('daily')
    uploads = []
    for section in sections:
        Tasks.DoTwitter(
            section, params, raw_data, hourly_data, daily_data, monthly_data,
            translation)
        if eval(params.get(section, 'underground', 'False')):
            from pywws import ToUnderground
            ToUnderground.ToUnderground(params, raw_data).Upload(True)
        uploads += Tasks.DoPlots(
            section, params, raw_data, hourly_data, daily_data, monthly_data,
            translation)
        uploads += Tasks.DoTemplates(
            section, params, raw_data, hourly_data, daily_data, monthly_data,
            translation)
    Upload.Upload(params, uploads)
    for file in uploads:
        os.unlink(file)
    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) > 1:
        print >>sys.stderr, 'Error: 0 or 1 arguments required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    elif len(args) == 1:
        data_dir = args[0]
    else:
        data_dir = '/data/weather'
    logger = ApplicationLogger(verbose)
    return Hourly(data_dir)
if __name__ == "__main__":
    sys.exit(main())
