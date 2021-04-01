# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-21  pywws contributors

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
the logging interval), :py:mod:`pywws.logdata` could be run quite
infrequently if you don't need up-to-date data.

There is no date or time information in the raw weather station data,
so :py:mod:`pywws.logdata` creates a time stamp for each reading. It
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

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.logdata [options] data_dir
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
import pprint
import sys
import time

from pywws.constants import SECOND, HOUR
import pywws.logger
import pywws.storage
from pywws.weatherstation import WeatherStation, WSDateTime

logger = logging.getLogger(__name__)


class DataLogger(object):
    def __init__(self, context):
        self.params = context.params
        self.status = context.status
        self.raw_data = context.raw_data
        # connect to weather station
        self.ws = WeatherStation(context=context)
        # check computer clock isn't earlier than last stored data
        self.last_stored_time = self.raw_data.before(
            datetime.max) or datetime.min
        if datetime.utcnow() < self.last_stored_time:
            raise ValueError('Computer time is earlier than last stored data')
        # infer pointer of last stored data
        saved_ptr = self.status.get('data', 'ptr')
        if saved_ptr:
            saved_ptr, sep, saved_date = saved_ptr.partition(',')
            if saved_ptr and saved_date:
                saved_ptr = int(saved_ptr, 16)
                saved_date = WSDateTime.from_csv(saved_date)
                saved_date = self.raw_data.nearest(saved_date)
                while saved_date < self.last_stored_time:
                    saved_date = self.raw_data.after(
                        saved_date + SECOND) or datetime.max
                    saved_ptr = self.ws.inc_ptr(saved_ptr)
                while saved_date > self.last_stored_time:
                    saved_date = self.raw_data.before(
                        saved_date - SECOND) or datetime.min
                    saved_ptr = self.ws.dec_ptr(saved_ptr)
            else:
                saved_ptr = None
        self.last_stored_ptr = saved_ptr
        self.check_fixed_block()

    def check_fixed_block(self):
        self.fixed_block = self.ws.get_fixed_block(unbuffered=True)
        # check 'magic number'
        if (self.fixed_block['magic_0'], self.fixed_block['magic_1']) not in (
                (0x55, 0xAA),):
            logger.critical("Unrecognised 'magic number' %02x %02x",
                            self.fixed_block['magic_0'],
                            self.fixed_block['magic_1'])
        # store info from fixed block
        if not self.params.get('config', 'pressure offset'):
            self.params.set('config', 'pressure offset', '%g' % (
                self.fixed_block['rel_pressure']
                    - self.fixed_block['abs_pressure']))
        self.status.set('fixed', 'fixed block', pprint.pformat(self.fixed_block))

    def fetch_logged(self, last_date, last_ptr):
        # offset last stored time by half logging interval
        last_stored = self.last_stored_time + timedelta(
            seconds=self.fixed_block['read_period'] * 30)
        if last_date <= last_stored:
            # nothing to do
            return
        # data_count includes record currently being updated every 48 seconds
        max_count = self.fixed_block['data_count'] - 1
        count = 0
        # initialise detection of data left after a station reboot
        saved_date = self.last_stored_time
        saved_ptr = self.last_stored_ptr
        self.last_stored_ptr = None
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
                else:
                    # potential duplicate data
                    duplicates.append(last_date)
                    saved_date = self.raw_data.before(saved_date)
                    saved_ptr = self.ws.dec_ptr(saved_ptr)
            if (data['delay'] is None or
                    data['delay'] > max(self.fixed_block['read_period'] * 2, 35)):
                logger.error('invalid data at %04x, %s',
                             last_ptr, last_date.isoformat(' '))
                last_date -= timedelta(minutes=self.fixed_block['read_period'])
            else:
                self.raw_data[last_date] = data
                count += 1
                last_date -= timedelta(minutes=data['delay'])
            last_ptr = self.ws.dec_ptr(last_ptr)
        if duplicates:
            for d in duplicates:
                del self.raw_data[d]
            count -= len(duplicates)
        last_date = self.raw_data.nearest(last_date) or datetime.max
        next_date = self.raw_data.after(last_date + SECOND)
        if next_date:
            gap = (next_date - last_date).seconds // 60
            gap -= self.fixed_block['read_period']
            if gap > 0:
                logger.critical("%d minutes gap in data detected", gap)
        logger.info("%d catchup records", count)

    def log_data(self, sync=None, clear=False):
        # get sync config value
        if sync is None:
            if self.fixed_block['read_period'] <= 5:
                sync = int(self.params.get('config', 'logdata sync', '1'))
            else:
                sync = int(self.params.get('config', 'logdata sync', '0'))
        # get address and date-time of last complete logged data
        logger.info('Synchronising to weather station')
        range_hi = datetime.max
        range_lo = datetime.min
        last_delay = self.ws.get_data(self.ws.current_pos())['delay']
        if last_delay > self.fixed_block['read_period'] + 1:
            # station is not logging correctly
            sync = 0
        if last_delay == 0:
            prev_date = datetime.min
        else:
            prev_date = datetime.utcnow()
        for data, last_ptr, logged in self.ws.live_data(logged_only=(sync > 1)):
            last_date = data['idx']
            logger.debug('Reading time %s', last_date.strftime('%H:%M:%S'))
            if logged:
                break
            if sync < 2 and self.ws._station_clock.clock:
                err = last_date - datetime.fromtimestamp(
                    self.ws._station_clock.clock)
                last_date -= timedelta(
                    minutes=data['delay'], seconds=err.seconds % 60)
                logger.debug('log time %s', last_date.strftime('%H:%M:%S'))
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
                logger.debug('est log time %s +- %ds (%s..%s)',
                             last_date.strftime('%H:%M:%S'), err.seconds,
                             lo.strftime('%H:%M:%S'), hi.strftime('%H:%M:%S'))
                if err < timedelta(seconds=15):
                    last_ptr = self.ws.dec_ptr(last_ptr)
                    break
        # go back through stored data, until we catch up with what we've already got
        logger.info('Fetching data')
        self.status.set(
            'data', 'ptr', '%06x,%s' % (last_ptr, last_date.isoformat(' ')))
        self.fetch_logged(last_date, last_ptr)
        if clear:
            logger.info('Clearing weather station memory')
            ptr = self.ws.fixed_format['data_count'][0]
            self.ws.write_data([(ptr, 1), (ptr+1, 0)])

    def live_data(self, logged_only=False):
        next_hour = datetime.utcnow(
            ).replace(minute=0, second=0, microsecond=0) + HOUR
        max_log_interval = timedelta(
            minutes=self.fixed_block['read_period'], seconds=66)
        for data, ptr, logged in self.ws.live_data(logged_only=logged_only):
            now = data['idx']
            if logged:
                self.raw_data[now] = data
                self.status.set(
                    'data', 'ptr', '%06x,%s' % (ptr, now.isoformat(' ')))
                if now >= self.last_stored_time + max_log_interval:
                    # fetch missing data
                    self.fetch_logged(now - timedelta(minutes=data['delay']),
                                      self.ws.dec_ptr(ptr))
                self.last_stored_time = now
            # don't supply live data if logged is overdue
            if now < self.last_stored_time + max_log_interval:
                yield data, logged
            if now >= next_hour:
                next_hour += HOUR
                self.check_fixed_block()


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(
            argv[1:], "hcs:v", ('help', 'clear', 'sync=', 'verbose'))
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 1
    # process options
    clear = False
    sync = None
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print(__usage__.strip())
            return 0
        elif o in ('-c', '--clear'):
            clear = True
        elif o in ('-s', '--sync'):
            sync = int(a)
        elif o in ('-v', '--verbose'):
            verbose += 1
    # check arguments
    if len(args) != 1:
        print('Error: 1 argument required\n', file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 2
    pywws.logger.setup_handler(verbose)
    root_dir = args[0]
    with pywws.storage.pywws_context(root_dir) as context:
        DataLogger(context).log_data(sync=sync, clear=clear)

if __name__ == "__main__":
    sys.exit(main())
