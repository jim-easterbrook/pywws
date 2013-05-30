#!/usr/bin/env python

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

"""conversions.py - a set of functions to convert pywws native units
(Centigrade, mm, m/s, hPa) to other popular units

"""

# rename imports to prevent them being imported when
# doing 'from pywws.conversions import *'
from pywws import Localisation as _Localisation

def illuminance_wm2(lux):
    "Approximate conversion of illuminance in lux to solar radiation in W/m2"
    if lux is None:
        return None
    return lux * 0.005

def pressure_inhg(hPa):
    "Convert pressure from hectopascals/millibar to inches of mercury"
    if hPa is None:
        return None
    return hPa / 33.86389

def rain_inch(mm):
    "Convert rainfall from millimetres to inches"
    if mm is None:
        return None
    return mm / 25.4

def temp_f(c):
    "Convert temperature from Celsius to Fahrenheit"
    if c is None:
        return None
    return (c * 9.0 / 5.0) + 32.0

def winddir_degrees(pts):
    "Convert wind direction from 0..15 to degrees"
    if pts is None:
        return None
    return pts * 22.5

_winddir_text_array = None

def winddir_text(pts):
    "Convert wind direction from 0..15 to compass point text"
    global _winddir_text_array
    if pts is None:
        return None
    if not _winddir_text_array:
        _ = _Localisation.translation.gettext
        _winddir_text_array = (
            _('N'), _('NNE'), _('NE'), _('ENE'),
            _('E'), _('ESE'), _('SE'), _('SSE'),
            _('S'), _('SSW'), _('SW'), _('WSW'),
            _('W'), _('WNW'), _('NW'), _('NNW'),
            )
    return _winddir_text_array[pts]

def wind_kmph(ms):
    "Convert wind from metres per second to kilometres per hour"
    if ms is None:
        return None
    return ms * 3.6

def wind_mph(ms):
    "Convert wind from metres per second to miles per hour"
    if ms is None:
        return None
    return ms * 3.6 / 1.609344

def wind_kn(ms):
    "Convert wind from metres per second to knots"
    if ms is None:
        return None
    return ms * 3.6 / 1.852

_bft_threshold = (
    0.3, 1.5, 3.4, 5.4, 7.9, 10.7, 13.8, 17.1, 20.7, 24.4, 28.4, 32.6)

def wind_bft(ms):
    "Convert wind from metres per second to Beaufort scale"
    if ms is None:
        return None
    for bft in range(len(_bft_threshold)):
        if ms < _bft_threshold[bft]:
            return bft
    return len(_bft_threshold)

def cadhumidex(temp, humidity):
    "Calculate Humidity Index as per Canadian Weather Standards"
    if temp is None or humidity is None:
        return None
    # Formulas are adapted to not use e^(...) with no appreciable
    # change in accuracy (0.0227%)
    saturation_pressure = (6.112 * (10.0**(7.5 * temp / (237.7 + temp))) *
                           float(humidity) / 100.0)
    return temp + (0.555 * (saturation_pressure - 10.0))

class Coordinate:
    LATITUDE = 1
    LONGITUDE = 2

def coordinates_loran(type, coord):
    """Converts decimal coordinates to LORAN format"""
    if type not in (Coordinate.LATITUDE, Coordinate.LONGITUDE):
        return None
    decimals = abs(coord) % 1
    degrees = abs(int(coord))
    minutes = "%.2f" % (decimals * 60)

    if type == Coordinate.LATITUDE:
        direction = 'N' if coord > 0 else 'S'
    elif type == Coordinate.LONGITUDE:
        direction = 'E' if coord > 0 else 'W'
        degrees = "%03d" % degrees

    return str(degrees) + minutes + direction

def latitude_loran(coord):
    """Converts decimal latitude to LORAN format"""
    if not isinstance(coord, (int, long, float, complex)):
        return None
    return coordinates_loran(Coordinate.LATITUDE, coord)

def longitude_loran(coord):
    """Converts decimal longitude to LORAN format"""
    if not isinstance(coord, (int, long, float, complex)):
        return None
    return coordinates_loran(Coordinate.LONGITUDE, coord)

def altitude_feet(meters):
    """Converts altitude in meters latitude to feet"""
    if not isinstance(meters, (int, long, float, complex)):
        return None
    return meters * 3.2808399;

def max_dec_length(input, max_length=0):
    """Converts a number to an integer that has `max_length` maximum digits"""
    if isinstance(input, (float, complex)):
        input = long(input)
    if not isinstance(input, (int, long)):
        return None
    if input < 0:
        max_length -= 1
    if max_length > 0:
        if abs(input) >= pow(10, max_length):
            return None
    return input

def _main(argv=None):
    global _winddir_text_array
    # run some simple tests
    print 'Wind speed:'
    print '%6s %8s %8s %8s %6s' % ('m/s', 'km/h', 'mph', 'knots', 'bft')
    for ms in (0, 1, 2, 4, 6, 9, 12, 15, 18, 22, 26, 30, 34):
        print '%6g %8.3f %8.3f %8.3f %6d' % (
            ms, wind_kmph(ms), wind_mph(ms), wind_kn(ms), wind_bft(ms))
    print 'Wind direction:'
    for pts in range(16):
        print winddir_text(pts),
    print
    print 'Wind direction, in Swedish:'
    _Localisation.SetTranslation('sv')
    _winddir_text_array = None
    for pts in range(16):
        print winddir_text(pts),
    print

if __name__ == "__main__":
    _main()
