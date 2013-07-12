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

import math

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

def pressure_trend_text(trend):
    """Convert pressure trend to a string, as used by the UK met
    office.

    """
    _ = _Localisation.translation.gettext
    if trend > 6.0:
        return _('rising very rapidly')
    elif trend > 3.5:
        return _('rising quickly')
    elif trend > 1.5:
        return _('rising')
    elif trend >= 0.1:
        return _('rising slowly')
    elif trend < -6.0:
        return _('falling very rapidly')
    elif trend < -3.5:
        return _('falling quickly')
    elif trend < -1.5:
        return _('falling')
    elif trend <= -0.1:
        return _('falling slowly')
    return _('steady')

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

def dew_point(temp, hum):
    """Compute dew point, using formula from
    http://en.wikipedia.org/wiki/Dew_point.

    """
    if temp is None or hum is None:
        return None
    a = 17.27
    b = 237.7
    gamma = ((a * temp) / (b + temp)) + math.log(float(hum) / 100.0)
    return (b * gamma) / (a - gamma)

def cadhumidex(temp, humidity):
    "Calculate Humidity Index as per Canadian Weather Standards"
    if temp is None or humidity is None:
        return None
    # Formulas are adapted to not use e^(...) with no appreciable
    # change in accuracy (0.0227%)
    saturation_pressure = (6.112 * (10.0**(7.5 * temp / (237.7 + temp))) *
                           float(humidity) / 100.0)
    return temp + (0.555 * (saturation_pressure - 10.0))

def usaheatindex(temp, humidity, dew):
    """Calculate Heat Index as per USA National Weather Service Standards

    See http://en.wikipedia.org/wiki/Heat_index, formula 1. The
    formula is not valid for T < 26.7C, Dew Point < 12C, or RH < 40%

    """
    if temp is None or humidity is None:
        return None
    if temp < 26.7 or humidity < 40 or dew < 12.0:
        return temp
    T = (temp * 1.8) + 32.0
    R = humidity
    c_1 = -42.379
    c_2 = 2.04901523
    c_3 = 10.14333127
    c_4 = -0.22475541
    c_5 = -0.00683783
    c_6 = -0.05481717
    c_7 = 0.00122874
    c_8 = 0.00085282
    c_9 = -0.00000199
    return ((c_1 + (c_2 * T) + (c_3 * R) + (c_4 * T * R) + (c_5 * (T**2)) +
             (c_6 * (R**2)) + (c_7 * (T**2) * R) + (c_8 * T * (R**2)) +
             (c_9 * (T**2) * (R**2))) - 32.0) / 1.8

def wind_chill(temp, wind):
    """Compute wind chill, using formula from
    http://en.wikipedia.org/wiki/wind_chill

    """
    if temp is None or wind is None:
        return None
    wind_kph = wind * 3.6
    if wind_kph <= 4.8 or temp > 10.0:
        return temp
    return min(13.12 + (temp * 0.6215) +
               (((0.3965 * temp) - 11.37) * (wind_kph ** 0.16)),
               temp)

def apparent_temp(temp, rh, wind):
    """Compute apparent temperature (real feel), using formula from
    http://www.bom.gov.au/info/thermal_stress/

    """
    if temp is None or rh is None or wind is None:
        return None
    vap_press = (float(rh) / 100.0) * 6.105 * math.exp(
        17.27 * temp / (237.7 + temp))
    return temp + (0.33 * vap_press) - (0.70 * wind) - 4.00

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
