#!/usr/bin/env python

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

"""conversions.py - a set of functions to convert pywws native units
(Centigrade, mm, m/s, hPa) to other popular units

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"

import math

import pywws.localisation
import pywws.process


def scale(value, factor):
    """Multiply value by factor, allowing for None values."""
    if value is None:
        return None
    return value * factor

def illuminance_wm2(lux):
    "Approximate conversion of illuminance in lux to solar radiation in W/m2"
    return scale(lux, 0.005)

def pressure_inhg(hPa):
    "Convert pressure from hectopascals/millibar to inches of mercury"
    return scale(hPa, 1 / 33.86389)

def pressure_trend_text(trend):
    """Convert pressure trend to a string, as used by the UK met
    office.

    """
    _ = pywws.localisation.translation.ugettext
    if trend > 6.0:
        return _(u'rising very rapidly')
    elif trend > 3.5:
        return _(u'rising quickly')
    elif trend > 1.5:
        return _(u'rising')
    elif trend >= 0.1:
        return _(u'rising slowly')
    elif trend < -6.0:
        return _(u'falling very rapidly')
    elif trend < -3.5:
        return _(u'falling quickly')
    elif trend < -1.5:
        return _(u'falling')
    elif trend <= -0.1:
        return _(u'falling slowly')
    return _(u'steady')

def rain_inch(mm):
    "Convert rainfall from millimetres to inches"
    return scale(mm, 1 / 25.4)

def temp_f(c):
    "Convert temperature from Celsius to Fahrenheit"
    if c is None:
        return None
    return (c * 9.0 / 5.0) + 32.0

def winddir_average(data, threshold, min_count, decay=1.0):
    """Compute average wind direction (in degrees) for a slice of data.

    The wind speed and direction of each data item is converted to a
    vector before averaging, so the result reflects the dominant wind
    direction during the time period covered by the data.

    Setting the ``decay`` parameter converts the filter from a simple
    averager to one where the most recent sample carries the highest
    weight, and earlier samples have a lower weight according to how
    long ago they were.

    This process is an approximation of "exponential smoothing". See
    `Wikipedia <http://en.wikipedia.org/wiki/Exponential_smoothing>`_
    for a detailed discussion.

    The parameter ``decay`` corresponds to the value ``(1 - alpha)``
    in the Wikipedia description. Because the weather data being
    smoothed may not be at regular intervals this parameter is the
    decay over 5 minutes. Weather data at other intervals will have
    its weight scaled accordingly.

    :note: The return value is in degrees, not the 0..15 range used
        elsewhere in pywws.

    :param data: a slice of pywws raw/calib or hourly data.

    :type data: pywws.storage.CoreStore

    :param threshold: minimum average windspeed for there to be a
        valid wind direction.

    :type threshold: float

    :param min_count: minimum number of data items for there to be a
        valid wind direction.

    :type min_count: int

    :param decay: filter coefficient decay rate.

    :type decay: float

    :rtype: float
    
    """
    wind_filter = pywws.process.WindFilter()
    count = 0
    for item in data:
        wind_filter.add(item)
        if item['wind_dir'] is not None:
            count += 1
    if count < min_count:
        return None
    speed, direction = wind_filter.result()
    if speed is None or speed < threshold:
        return None
    return direction * 22.5
    
def winddir_degrees(pts):
    "Convert wind direction from 0..15 to degrees"
    return scale(pts, 22.5)

_winddir_text_array = None

def winddir_text(pts):
    "Convert wind direction from 0..15 to compass point text"
    global _winddir_text_array
    if pts is None:
        return None
    if not isinstance(pts, int):
        pts = int(pts + 0.5) % 16
    if not _winddir_text_array:
        _ = pywws.localisation.translation.ugettext
        _winddir_text_array = (
            _(u'N'), _(u'NNE'), _(u'NE'), _(u'ENE'),
            _(u'E'), _(u'ESE'), _(u'SE'), _(u'SSE'),
            _(u'S'), _(u'SSW'), _(u'SW'), _(u'WSW'),
            _(u'W'), _(u'WNW'), _(u'NW'), _(u'NNW'),
            )
    return _winddir_text_array[pts]

def wind_kmph(ms):
    "Convert wind from metres per second to kilometres per hour"
    return scale(ms, 3.6)

def wind_mph(ms):
    "Convert wind from metres per second to miles per hour"
    return scale(ms, 3.6 / 1.609344)

def wind_kn(ms):
    "Convert wind from metres per second to knots"
    return scale(ms, 3.6 / 1.852)

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

def usaheatindex(temp, humidity, dew=None):
    """Calculate Heat Index as per USA National Weather Service Standards

    See http://en.wikipedia.org/wiki/Heat_index, formula 1. The
    formula is not valid for T < 26.7C, Dew Point < 12C, or RH < 40%

    """
    if temp is None or humidity is None:
        return None
    if dew is None:
        dew = dew_point(temp, humidity)
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

def cloud_base(temp, hum):
    """Calculate cumulus cloud base in metres, using formula from
    https://en.wikipedia.org/wiki/Cloud_base or
    https://de.wikipedia.org/wiki/Kondensationsniveau#Konvektionskondensationsniveau
    """
    if temp is None or hum is None:
        return None
    dew_pt = dew_point(temp, hum)
    spread = float(temp) - dew_pt
    return spread * 125.0

def cloud_ft(m):
    "Convert cloud base from metres to feet."
    return scale(m, 3.28084)


def _main(argv=None):
    global _winddir_text_array
    # run some simple tests
    print('Wind speed:')
    print('%6s %8s %8s %8s %6s' % ('m/s', 'km/h', 'mph', 'knots', 'bft'))
    for ms in (0, 1, 2, 4, 6, 9, 12, 15, 18, 22, 26, 30, 34):
        print('%6g %8.3f %8.3f %8.3f %6d' % (
            ms, wind_kmph(ms), wind_mph(ms), wind_kn(ms), wind_bft(ms)))
    print('Wind direction:')
    for pts in range(16):
        print(' ' + winddir_text(pts), end='')
    print('')
    print('Wind direction, in Swedish:')
    pywws.localisation.set_translation('sv')
    _winddir_text_array = None
    for pts in range(16):
        print(' ' + winddir_text(pts), end='')
    print('')
    print('Cloud base in m and ft:')
    for hum in range(25, 75, 5):
        print("%8.3f m / %8.3f ft" % (cloud_base(15.0, hum), cloud_ft(cloud_base(15.0, hum))))
    print('')


if __name__ == "__main__":
    _main()
