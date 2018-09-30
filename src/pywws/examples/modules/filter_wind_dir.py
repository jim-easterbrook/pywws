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

from datetime import timedelta

import pywws.process

class Calib(object):
    """Weather station calibration class with wind direction filter."""
    def __init__(self, params, raw_data):
        self.pressure_offset = float(params.get('config', 'pressure offset'))
        self.raw_data = raw_data
        self.wind_fil_aperture = timedelta(minutes=29)

    def calib(self, raw):
        result = dict(raw)
        # calculate relative pressure
        result['rel_pressure'] = result['abs_pressure'] + self.pressure_offset
        # filter wind direction
        stop = result['idx']
        start = stop - self.wind_fil_aperture
        wind_filter = pywws.process.WindFilter(decay=0.8)
        for data in self.raw_data[start:stop]:
            wind_filter.add(data)
        wind_filter.add(raw)
        speed, result['wind_dir'] = wind_filter.result()
        return result
