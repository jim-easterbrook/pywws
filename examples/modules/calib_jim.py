# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

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
    def __init__(self, params):
        # pressure sensor went wrong on 19th August 2011
        self.pressure_fault = datetime(2011, 8, 19, 11, 0, 0)

    def calib(self, raw):
        result = dict(raw)
        # sanitise data
        if result['wind_dir'] is not None and result['wind_dir'] >= 16:
            result['wind_dir'] = None
        # pressure readings are nonsense since sensor failed
        if raw['idx'] < self.pressure_fault:
            result['rel_pressure'] = raw['abs_pressure'] + 7.4
        else:
            result['abs_pressure'] = None
            result['rel_pressure'] = None
        return result
