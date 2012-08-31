#!/usr/bin/env python

"""conversions.py - a set of functions to convert pywws native units
(Centigrade, mm, m/s, hPa) to other popular units

"""

# rename imports to prevent them being imported when
# doing 'from pywws.conversions import *'
import Localisation as _Localisation

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

if __name__ == "__main__":
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
