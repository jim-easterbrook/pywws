#!/usr/bin/env python

"""
Post weather update to WOW from the Met Office UK.

usage: python ToMetOffice.py [options] data_dir
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

class ToMetOffice(toservice.ToService):
    def __init__(self, params, calib_data):
        self.config_section = 'metoffice'
        toservice.ToService.__init__(self, params, calib_data)
        # UK Met Office 'WOW' server
        self.server = 'http://wow.metoffice.gov.uk/automaticreading'
        # set fixed part of upload data
        siteid = self.params.get(self.config_section, 'site id')
        siteAuthenticationKey = self.params.get(self.config_section, 'aws pin')
        self.fixed_data = {
            'siteid'                : siteid,
            'siteAuthenticationKey' : siteAuthenticationKey,
            'softwaretype'          : 'pywws'
            }

    def Upload(self, catchup):
        return self._upload(self.server, self.fixed_data, catchup)

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
    return ToMetOffice(
        DataStore.params(args[0]), DataStore.calib_store(args[0])
        ).Upload(catchup)

if __name__ == "__main__":
    sys.exit(main())
