#!/usr/bin/env python

def _(msg) : return msg

forecast_text = {
    'A' : _("Settled fine"),
    'B' : _("Fine weather"),
    'C' : _("Becoming fine"),
    'D' : _("Fine, becoming less settled"),
    'E' : _("Fine, possible showers"),
    'F' : _("Fairly fine, improving"),
    'G' : _("Fairly fine, possible showers early"),
    'H' : _("Fairly fine, showery later"),
    'I' : _("Showery early, improving"),
    'J' : _("Changeable, mending"),
    'K' : _("Fairly fine, showers likely"),
    'L' : _("Rather unsettled clearing later"),
    'M' : _("Unsettled, probably improving"),
    'N' : _("Showery, bright intervals"),
    'O' : _("Showery, becoming less settled"),
    'P' : _("Changeable, some rain"),
    'Q' : _("Unsettled, short fine intervals"),
    'R' : _("Unsettled, rain later"),
    'S' : _("Unsettled, some rain"),
    'T' : _("Mostly very unsettled"),
    'U' : _("Occasional rain, worsening"),
    'V' : _("Rain at times, very unsettled"),
    'W' : _("Rain at frequent intervals"),
    'X' : _("Rain, very unsettled"),
    'Y' : _("Stormy, may improve"),
    'Z' : _("Stormy, much rain")
    }

del _

def ZambrettiCode(pressure, month, wind, trend,
                  north=True, baro_top=1050.0, baro_bottom=950.0):
    """Simple implementation of Zambretti forecaster algorithm.
    Inspired by beteljuice.com Java algorithm, as converted to Python by
    honeysucklecottage.me.uk, and further information
    from http://www.meteormetrics.com/zambretti.htm"""
    # normalise pressure
    pressure = 950.0 + ((1050.0 - 950.0) *
                        (pressure - baro_bottom) / (baro_top - baro_bottom))
    # adjust pressure for wind direction
    if wind != None:
        if not north:
            # southern hemisphere, so add 180 degrees
            wind = (wind + 8) % 16
        pressure += (  5.2,  4.2,  3.2,  1.05, -1.1, -3.15, -5.2, -8.35,
                     -11.5, -9.4, -7.3, -5.25, -3.2, -1.15,  0.9,  3.05)[wind]
    # compute base forecast from pressure and trend (hPa / hour)
    if trend >= 0.1:
        # rising pressure
        if north == (month >= 4 and month <= 9):
            pressure += 3.2
        F = 0.1740 * (1031.40 - pressure)
        LUT = ('A', 'B', 'B', 'C', 'F', 'G', 'I', 'J', 'L', 'M', 'M', 'Q', 'T',
               'Y')
    elif trend <= -0.1:
        # falling pressure
        if north == (month >= 4 and month <= 9):
            pressure -= 3.2
        F = 0.1553 * (1029.95 - pressure)
        LUT = ('B', 'D', 'H', 'O', 'R', 'U', 'V', 'X', 'X', 'Z')
    else:
        # steady
        F = 0.2314 * (1030.81 - pressure)
        LUT = ('A', 'B', 'B', 'B', 'E', 'K', 'N', 'N', 'P', 'P', 'S', 'W', 'W',
               'X', 'X', 'X', 'Z')
    # clip to range of lookup table
    F = min(max(int(F + 0.5), 0), len(LUT) - 1)
    # convert to letter code
    return LUT[F]

def ZambrettiText(letter):
    return forecast_text[letter]

if __name__ == "__main__":
    import WeatherStation
    wind_dir = WeatherStation.get_wind_dir_text()
    for pressure in range(1030, 960, -10):
        for trend_txt in ('S', 'R-S', 'R-W', 'F-W', 'F-S'):
            trend, month = {
                'R-W' : ( 0.2, 1),
                'F-W' : (-0.2, 1),
                'R-S' : ( 0.2, 7),
                'F-S' : (-0.2, 7),
                'S'   : ( 0.0, 7),
                }[trend_txt]
            for wind in (0, 2, 14, None, 4, 12, 6, 10, 8):
                if wind == None:
                    wind_txt = 'calm'
                else:
                    wind_txt = wind_dir[wind]
                print '%4d %4s %4s  %3s' % (
                    pressure, trend_txt, wind_txt,
                    ZambrettiCode(pressure, month, wind, trend))
        print ''
