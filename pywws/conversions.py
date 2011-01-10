"""
A set of functions to convert pywws native units (Centigrade, mm, m/s, hPa) to
other popular units.
"""

def pressure_inhg(hPa):
    "Convert pressure from hectopascals/millibar to inches of mercury"
    return hPa / 33.86389

def rain_inch(mm):
    "Convert rainfall from millimetres to inches"
    return mm / 25.4

def temp_f(c):
    "Convert temperature from Celsius to Fahrenheit"
    return (c * 9.0 / 5.0) + 32.0

def wind_kmph(ms):
    "Convert (wind) wind from metres per second to kilometres per hour"
    return ms * 3.6

def wind_mph(ms):
    "Convert (wind) wind from metres per second to miles per hour"
    return ms * 3.6 / 1.609344

def wind_kn(ms):
    "Convert (wind) wind from metres per second to knots"
    return ms * 3.6 / 1.852

def wind_bft(ms):
    "Convert (wind) wind from metres per second to Beaufort scale"
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
