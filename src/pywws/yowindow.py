# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-18  pywws contributors

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

"""Generate YoWindow XML file
::

%s

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.yowindow [options] data_dir output_file
 options are:
  -h or --help     display this help
  -v or --verbose  increase amount of reassuring messages
 data_dir is the root directory of the weather data
 output_file is the YoWindow XML file to be written
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import logging
import sys
from datetime import datetime, timedelta

from pywws.conversions import apparent_temp
import pywws.logger
import pywws.storage
import pywws.timezone


class YoWindow(object):
    """Class to write YoWindow XML file.

    For file spec see http://yowindow.com/doc/yowindow_pws_format.xml
    """
    def __init__(self, calib_data):
        self.data = calib_data
        # compute local midnight
        self.midnight = datetime.utcnow().replace(
            tzinfo=pywws.timezone.utc).astimezone(
                pywws.timezone.Local).replace(
                    hour=0, minute=0, second=0).astimezone(
                        pywws.timezone.utc).replace(tzinfo=None)
        self.day = timedelta(hours=24)
        self.hour = timedelta(hours=1)
        self.last_update = None

    def write_file(self, file_name, data=None):
        if not data:
            data = self.data[self.data.before(datetime.max)]
        data_hour = self.data[self.data.nearest(data['idx'] - self.hour)]
        while data['idx'] < self.midnight:
            self.midnight -= self.day
        while data['idx'] >= self.midnight + self.day:
            self.midnight += self.day
        data_midnight = self.data[self.data.before(self.midnight)]
        of = open(file_name, 'w')
        of.write('<response>\n')
        of.write('  <current_weather>\n')
        if data['temp_out'] != None:
            of.write('    <temperature unit="c">\n')
            of.write('      <current value="%.1f"/>\n' % (data['temp_out']))
            if data['hum_out'] != None and data['wind_ave'] != None:
                of.write('      <feels_like value="%.1f"/>\n' % (
                    apparent_temp(
                        data['temp_out'], data['hum_out'], data['wind_ave'])))
            of.write('    </temperature>\n')
        if data['hum_out'] != None:
            of.write('    <humidity value="%d"/>\n' % (data['hum_out']))
        of.write('    <pressure value="%.1f" trend="%.1f" unit="hPa"/>\n' % (
            data['rel_pressure'],
            data['rel_pressure'] - data_hour['rel_pressure']))
        if data['wind_ave'] != None:
            of.write('    <wind>\n')
            of.write('      <speed value="%.1f" unit="m/s"/>\n' % (
                data['wind_ave']))
            if data['wind_dir'] != None and data['wind_dir'] < 16:
                of.write('      <direction value="%.0f"/>\n' % (
                    data['wind_dir'] * 22.5))
            if data['wind_gust'] != None:
                of.write('      <gusts value="%.1f" unit="m/s"/>\n' % (
                    data['wind_gust']))
            of.write('    </wind>\n')
        of.write('    <sky>\n')
        of.write('      <precipitation>\n')
        of.write('        <rain>\n')
        of.write('          <rate value="%.1f" unit="mm"/>\n' % (
            max(data['rain'] - data_hour['rain'], 0.0)))
        of.write('          <daily_total value="%.1f" unit="mm"/>\n' % (
            max(data['rain'] - data_midnight['rain'], 0.0)))
        of.write('        </rain>\n')
        of.write('      </precipitation>\n')
        of.write('    </sky>\n')
        of.write('    <auto_update>\n')
        if self.last_update:
            interval = (data['idx'] - self.last_update).seconds
        else:
            interval = data['delay'] * 60
        self.last_update = data['idx']
        of.write('      <interval value="%d"/>\n' % (interval))
        of.write('    </auto_update>\n')
        of.write('  </current_weather>\n')
        of.write('</response>\n')
        of.close()


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print(__usage__.strip())
            return 0
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 2:
        print("Error: 2 arguments required", file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 2
    pywws.logger.setup_handler(verbose)
    with pywws.storage.pywws_context(args[0]) as context:
        return YoWindow(context.calib_data).write_file(args[1])


if __name__ == "__main__":
    sys.exit(main())
