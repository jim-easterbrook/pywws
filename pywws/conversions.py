"""
A set of functions to convert pywws native units (Centigrade, mm, m/s, hPa) to
other popular units.
"""

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

def wind_bft(ms):
    "Convert wind from metres per second to Beaufort scale"
    if ms is None:
        return None
    if ms < 0.3:
        return 0
    elif ms <= 1.5:
        return 1
    elif ms <= 3.4:
        return 2
    elif ms <= 5.4:
        return 3
    elif ms <= 7.9:
        return 4
    elif ms <= 10.7:
        return 5
    elif ms <= 13.8:
        return 6
    elif ms <= 17.1:
        return 7
    elif ms <= 20.7:
        return 8
    elif ms <= 24.4:
        return 9
    elif ms <= 28.4:
        return 10
    elif ms <= 32.6:
        return 11
    return 12
