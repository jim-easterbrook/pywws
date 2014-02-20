# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-14  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

from datetime import datetime

class Calib(object):
    """Jim's weather station calibration class."""
    def __init__(self, params, raw_data):
        # pressure sensor went wrong on 19th August 2011
        self.pressure_fault = datetime(2011, 8, 19, 11, 0, 0)
        # finally replaced weather station on 11th November 2011
        self.new_station = datetime(2011, 11, 11, 12, 5, 0)

    def calib(self, raw):
        result = dict(raw)
        # set relative pressure and tweak temperature and humidity to make old
        # and new stations closer
        if result['idx'] > self.new_station:
            result['rel_pressure'] = result['abs_pressure'] + 5.2
            if result['temp_out'] is not None:
                result['temp_out'] += 0.6
            if result['hum_out'] is not None:
                result['hum_out'] -= 1
        else:
            if result['idx'] > self.pressure_fault:
                # pressure readings are nonsense since sensor failed
                result['abs_pressure'] = None
                result['rel_pressure'] = None
            else:
                result['rel_pressure'] = result['abs_pressure'] + 7.4
            if result['temp_out'] is not None:
                result['temp_out'] -= 0.6
            if result['hum_out'] is not None:
                result['hum_out'] += 2
        return result
