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

"""Test quality of USB connection to weather station

::

%s

The USB link to my weather station is not 100%% reliable. The data
read from the station by the computer is occasionally corrupted,
perhaps by interference. I've been trying to solve this by putting
ferrite beads around the USB cable and relocating possible
interference sources such as external hard drives. All without any
success so far.

This program tests the USB connection for errors by continuously
reading the entire weather station memory (except for those parts that
may be changing) looking for errors. Each 32-byte block is read twice,
and if the two readings differ a warning message is displayed. Also
displayed are the number of blocks read, and the number of errors
found.

I typically get one or two errors per hour, so the test needs to be
run for several hours to produce a useful measurement. Note that other
software that accesses the weather station (such as
:py:mod:`pywws.hourly` or :py:mod:`pywws.livelog`)
must not be run while the test is in progress.

If you run this test and get no errors at all, please let me know.
There is something good about your setup and I'd love to know what it
is!

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"

__usage__ = """
 usage: python -m pywws.usbtest [options]
 options are:
  -h | --help           display this help
  -v | --verbose        increase amount of reassuring messages
                        (repeat for even more messages e.g. -vvv)
"""

__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import sys

import pywws.logger
import pywws.weatherstation


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ('help', 'verbose'))
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 1
    # check arguments
    if len(args) != 0:
        print('Error: no arguments allowed\n', file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 2
    # process options
    verbose = 0
    for o, a in opts:
        if o in ('-h', '--help'):
            print(__usage__.strip())
            return 0
        elif o in ('-v', '--verbose'):
            verbose += 1
    # do it!
    pywws.logger.setup_handler(verbose)
    ws = pywws.weatherstation.WeatherStation()
    fixed_block = ws.get_fixed_block()
    if not fixed_block:
        print("No valid data block found")
        return 3
    # loop
    ptr = ws.data_start
    total_count = 0
    bad_count = 0
    while True:
        if total_count % 1000 == 0:
            active = ws.current_pos()
        while True:
            ptr += 0x20
            if ptr >= 0x10000:
                ptr = ws.data_start
            if active < ptr - 0x10 or active >= ptr + 0x20:
                break
        result_1 = ws._read_block(ptr, retry=False)
        result_2 = ws._read_block(ptr, retry=False)
        if result_1 != result_2:
            logger.warning('read_block changing %06x', ptr)
            logger.warning('  %s', str(result_1))
            logger.warning('  %s', str(result_2))
            bad_count += 1
        total_count += 1
        print("\r %d/%d " % (bad_count, total_count), end='', flush=True)
    print('')
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
