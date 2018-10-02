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
import logging

from pywws.constants import SECOND

logger = logging.getLogger(__name__)

MINUTEx30 = timedelta(minutes=30)

class Calib(object):
    """Weather station calibration class with temperature spike removal."""
    def __init__(self, params, raw_data):
        self.raw_data = raw_data
        self.pressure_offset = float(params.get('config', 'pressure offset'))

    def calib(self, raw):
        result = dict(raw)
        # try to remove spikes in outside temperature
        if result['temp_out'] is not None:
            # get last 30 mins valid temperatures
            history = []
            for data in self.raw_data[result['idx'] - MINUTEx30:
                                      result['idx'] + SECOND]:
                if data['temp_out'] is not None:
                    history.append(data['temp_out'])
            history.sort()
            if len(history) >= 4:
                median = history[(len(history) - 1) / 2]
                if abs(result['temp_out'] - median) > 1.5:
                    logger.warning(
                        'spike? %s %s', str(history), str(result['temp_out']))
                if abs(result['temp_out'] - median) > 2.0:
                    result['temp_out'] = None
        # calculate relative pressure
        result['rel_pressure'] = result['abs_pressure'] + self.pressure_offset
        return result
