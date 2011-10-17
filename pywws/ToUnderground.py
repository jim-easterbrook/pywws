#!/usr/bin/env python

"""
Post weather update to WeatherUnderground.

usage: python ToUnderground.py [options] data_dir
options are:
  -h or --help     display this help
  -c or --catchup  upload all data since last upload (up to 4 weeks)
  -v or --verbose  increase amount of reassuring messages
data_dir is the root directory of the weather data

StationID and password are read from the weather.ini file in data_dir.
"""

import getopt
import logging
import socket
import sys
import urllib
from datetime import datetime, timedelta

import conversions
import DataStore
from Logger import ApplicationLogger
from TimeZone import Local, utc
import toservice
from WeatherStation import dew_point

FIVE_MINS = timedelta(minutes=5)

class ToUnderground(toservice.ToService):
    def __init__(self, params, calib_data):
        self.config_section = 'underground'
        toservice.ToService.__init__(self, params, calib_data)
        # Weather Underground server, normal and rapid fire
        self.server = 'http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
        self.server_rf = 'http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php'
        # set fixed part of upload data, versions for normal and rapid fire
        password = self.params.get(
            self.config_section, 'password', 'undergroudpassword')
        station = self.params.get(
            self.config_section, 'station', 'undergroundstation')
        self.fixed_data = {
            'action'       : 'updateraw',
            'ID'           : station,
            'PASSWORD'     : password,
            'softwaretype' : 'pywws',
            }
        self.fixed_data_rf = dict(self.fixed_data)
        self.fixed_data_rf['realtime'] = '1'
        self.fixed_data_rf['rtfreq'] = '48'

    def Upload(self, catchup):
        return self._upload(self.server, self.fixed_data, catchup)

    def RapidFire(self, data, catchup):
        last_log = self.data.before(datetime.max)
        if last_log < data['idx'] - FIVE_MINS:
            # logged data is not (yet) up to date
            return True
        if catchup:
            last_update = self.params.get_datetime(
                self.config_section, 'last update')
            if not last_update:
                last_update = datetime.min
            if last_update <= last_log - FIVE_MINS:
                # last update was well before last logged data
                if not self.Upload(True):
                    return False
        if not self._send_data(data, self.server_rf, self.fixed_data_rf):
            return False
        self.params.set(
            self.config_section, 'last update', data['idx'].isoformat(' '))
        return True

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hcv", ['help', 'catchup', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    catchup = False
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
        elif o == '-c' or o == '--catchup':
            catchup = True
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, "Error: 1 argument required"
        print >>sys.stderr, __doc__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    return ToUnderground(
        DataStore.params(args[0]), DataStore.calib_store(args[0])
        ).Upload(catchup)

if __name__ == "__main__":
    sys.exit(main())
