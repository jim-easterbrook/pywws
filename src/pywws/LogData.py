#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-16 pywws contributors

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

"""Save weather station history to file
::

%s

This module gets data from the weather station's memory and stores it
to file. Each time it is run it fetches all data that is newer than
the last stored data, so it only needs to be run every hour or so. As
the weather station typically stores two weeks' readings (depending on
the logging interval), :py:mod:`pywws.LogData` could be run quite
infrequently if you don't need up-to-date data.

There is no date or time information in the raw weather station data,
so :py:mod:`pywws.LogData` creates a time stamp for each reading. It
uses the computer's clock, rather than the weather station clock which
can not be read accurately by the computer. A networked computer
should have its clock set accurately by `ntp
<http://en.wikipedia.org/wiki/Network_Time_Protocol>`_.

Synchronisation with the weather station is achieved by waiting for a
change in the current data. There are two levels of synchronisation,
set by the config file or a command line option. Level 0 is quicker,
but is only accurate to around twelve seconds. Level 1 waits until the
weather station stores a new logged record, and gets time stamps
accurate to a couple of seconds. Note that this could take a long
time, if the logging interval is greater than the recommended five
minutes.

Detailed API
------------

"""

from __future__ import absolute_import

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.LogData [options] data_dir
 options are:
  -h   | --help     display this help
  -c   | --clear    clear weather station's memory full indicator
  -s n | --sync n   set quality of synchronisation to weather station (0 or 1)
  -v   | --verbose  increase number of informative messages
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

from datetime import datetime, timedelta
import getopt
import logging
import os
import sys
import time

from pywws.constants import SECOND, HOUR
from pywws import DataStore
from pywws.Logger import ApplicationLogger
from pywws.WeatherStation import weather_station

class DataLogger(object):
    def __init__(self, params, status, raw_data):
        self.logger = logging.getLogger('pywws.DataLogger')
        self.params = params
        self.status = status
        self.raw_data = raw_data
        # connect to weather station
        ws_type = self.params.get('fixed', 'ws type')
        if ws_type:
            self.params.unset('fixed', 'ws type')
            self.params.set('config', 'ws type', ws_type)
        ws_type = self.params.get('config', 'ws type', 'Unknown')
        avoid = eval(self.params.get('config', 'usb activity margin', '3.0'))
        self.ws = weather_station(
            ws_type=ws_type, status=self.status, avoid=avoid)
        # check for valid weather station type
        fixed_block = self.check_fixed_block()
        if ws_type not in ('1080', '3080'):
            print "Unknown weather station type. Please edit weather.ini"
            print "and set 'ws type' to '1080' or '3080', as appropriate."
            if fixed_block['lux_wm2_coeff'] == 0.0:
                print "Your station is probably a '1080' type."
            else:
                print "Your station is probably a '3080' type."
            sys.exit(1)
        # check computer clock isn't earlier than last stored data
        last_stored = self.raw_data.before(datetime.max)
        if last_stored and datetime.utcnow() < last_stored:
            raise ValueError('Computer time is earlier than last stored data')

    def check_fixed_block(self):
        fixed_block = self.ws.get_fixed_block(unbuffered=True)
        # check 'magic number'
        if (fixed_block['magic_0'], fixed_block['magic_1']) not in (
                (0x55, 0xAA),):
            self.logger.critical("Unrecognised 'magic number' %02x %02x",
                                 fixed_block['magic_0'], fixed_block['magic_1'])
        # store info from fixed block
        self.status.unset('fixed', 'pressure offset')
        if not self.params.get('config', 'pressure offset'):
            self.params.set('config', 'pressure offset', '%g' % (
                fixed_block['rel_pressure'] - fixed_block['abs_pressure']))
        self.params.unset('fixed', 'fixed block')
        self.status.set('fixed', 'fixed block', str(fixed_block))
        return fixed_block

    def catchup(self, last_date, last_ptr):
        fixed_block = self.ws.get_fixed_block(unbuffered=True)
        # get time to go back to
        last_stored = self.raw_data.before(datetime.max)
        if not last_stored:
            last_stored = datetime.min
        if self.status.get('data', 'ptr'):
            saved_ptr, saved_date = self.status.get('data', 'ptr').split(',')
            saved_ptr = int(saved_ptr, 16)
            saved_date = DataStore.safestrptime(saved_date)
            saved_date = self.raw_data.nearest(saved_date)
            while saved_date < last_stored:
                saved_date = self.raw_data.after(saved_date + SECOND)
                saved_ptr = self.ws.inc_ptr(saved_ptr)
        else:
            saved_ptr = None
            saved_date = None
        last_stored += timedelta(seconds=fixed_block['read_period'] * 30)
        if last_date <= last_stored:
            # nothing to do
            return
        self.status.set(
            'data', 'ptr', '%06x,%s' % (last_ptr, last_date.isoformat(' ')))
        # data_count includes record currently being updated every 48 seconds
        max_count = fixed_block['data_count'] - 1
        count = 0
        duplicates = []
        while last_date > last_stored and count < max_count:
            data = self.ws.get_data(last_ptr)
            if last_ptr == saved_ptr:
                if any(data[key] != self.raw_data[saved_date][key] for key in (
                        'hum_in', 'temp_in', 'hum_out', 'temp_out',
                        'abs_pressure', 'wind_ave', 'wind_gust', 'wind_dir',
                        'rain', 'status')):
                    # pointer matches but data is different, so no duplicates
                    duplicates = None
                    saved_ptr = None
                    saved_date = None
                else:
                    # potential duplicate data
                    duplicates.append(last_date)
                    saved_date = self.raw_data.before(saved_date)
                    saved_ptr = self.ws.dec_ptr(saved_ptr)
            if (data['delay'] is None or
                    data['delay'] > max(fixed_block['read_period'] * 2, 35)):
                self.logger.error('invalid data at %04x, %s',
                                  last_ptr, last_date.isoformat(' '))
                last_date -= timedelta(minutes=fixed_block['read_period'])
            else:
                self.raw_data[last_date] = data
                count += 1
                last_date -= timedelta(minutes=data['delay'])
            last_ptr = self.ws.dec_ptr(last_ptr)
        if duplicates:
            for d in duplicates:
                del self.raw_data[d]
            count -= len(duplicates)
        last_date = self.raw_data.nearest(last_date)
        next_date = self.raw_data.after(last_date + SECOND)
        if next_date:
            gap = (next_date - last_date).seconds // 60
            gap -= fixed_block['read_period']
            if gap > 0:
                self.logger.critical("%d minutes gap in data detected", gap)
        self.logger.info("%d catchup records", count)

    def log_data(self, sync=None, clear=False):
        fixed_block = self.check_fixed_block()
        # get sync config value
        if sync is None:
            if fixed_block['read_period'] <= 5:
                sync = int(self.params.get('config', 'logdata sync', '1'))
            else:
                sync = int(self.params.get('config', 'logdata sync', '0'))
        # get address and date-time of last complete logged data
        self.logger.info('Synchronising to weather station')
        range_hi = datetime.max
        range_lo = datetime.min
        last_delay = self.ws.get_data(self.ws.current_pos())['delay']
        if last_delay == 0:
            prev_date = datetime.min
        else:
            prev_date = datetime.utcnow()
        for data, last_ptr, logged in self.ws.live_data(logged_only=(sync > 1)):
            last_date = data['idx']
            self.logger.debug('Reading time %s', last_date.strftime('%H:%M:%S'))
            if logged:
                break
            if sync < 2 and self.ws._station_clock.clock:
                err = last_date - datetime.fromtimestamp(
                    self.ws._station_clock.clock)
                last_date -= timedelta(
                    minutes=data['delay'], seconds=err.seconds % 60)
                self.logger.debug('log time %s', last_date.strftime('%H:%M:%S'))
                last_ptr = self.ws.dec_ptr(last_ptr)
                break
            if sync < 1:
                hi = last_date - timedelta(minutes=data['delay'])
                if last_date - prev_date > timedelta(seconds=50):
                    lo = hi - timedelta(seconds=60)
                elif data['delay'] == last_delay:
                    lo = hi - timedelta(seconds=60)
                    hi = hi - timedelta(seconds=48)
                else:
                    lo = hi - timedelta(seconds=48)
                last_delay = data['delay']
                prev_date = last_date
                range_hi = min(range_hi, hi)
                range_lo = max(range_lo, lo)
                err = (range_hi - range_lo) / 2
                last_date = range_lo + err
                self.logger.debug('est log time %s +- %ds (%s..%s)',
                                  last_date.strftime('%H:%M:%S'), err.seconds,
                                  lo.strftime('%H:%M:%S'), hi.strftime('%H:%M:%S'))
                if err < timedelta(seconds=15):
                    last_ptr = self.ws.dec_ptr(last_ptr)
                    break
        # go back through stored data, until we catch up with what we've already got
        self.logger.info('Fetching data')
        self.catchup(last_date, last_ptr)
        if clear:
            self.logger.info('Clearing weather station memory')
            ptr = self.ws.fixed_format['data_count'][0]
            self.ws.write_data([(ptr, 1), (ptr+1, 0)])

    def live_data(self, logged_only=False):
        next_hour = datetime.utcnow(
            ).replace(minute=0, second=0, microsecond=0) + HOUR
        next_ptr = None
        for data, ptr, logged in self.ws.live_data(logged_only=logged_only):
            if logged:
                now = data['idx']
                if ptr == next_ptr:
                    # data is contiguous with last logged value
                    self.raw_data[now] = data
                    if now >= next_hour:
                        next_hour += HOUR
                        self.check_fixed_block()
                    self.status.set(
                        'data', 'ptr', '%06x,%s' % (ptr, now.isoformat(' ')))
                else:
                    # catch up missing data
                    self.catchup(now, ptr)
                next_ptr = self.ws.inc_ptr(ptr)
            yield data, logged

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(
            argv[1:], "hcs:v", ('help', 'clear', 'sync=', 'verbose'))
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    clear = False
    sync = None
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
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
        print >>sys.stderr, __usage__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    root_dir = args[0]
    DataLogger(
        DataStore.params(root_dir), DataStore.status(root_dir),
        DataStore.data_store(root_dir)).log_data(sync=sync, clear=clear)

if __name__ == "__main__":
    sys.exit(main())
