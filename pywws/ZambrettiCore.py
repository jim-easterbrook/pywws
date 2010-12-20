#!/usr/bin/env python

# honeysucklecottage.me.uk - Python port of beteljuice
# javascript forecaster. Comes with no warranty of any kind.

# Further tweaking / Pythonification by Jim Easterbrook

# beteljuice.com - near enough Zambretti Algorhithm
# June 2008 - v1.0
# tweak added so decision # can be output

# Negretti and Zambras 'slide rule' is supposed to be better than 90% accurate
# for a local forecast upto 12 hrs, it is most accurate in the temperate zones and about 09:00  hrs local solar time.
# I hope I have been able to 'tweak it' a little better ;-)

# This code is free to use and redistribute as long as NO CHARGE is EVER made for its use or output

import math

# usage: forecast = Zambretti(z_hpa, z_month, z_wind, z_trend
#                             [, z_north ] [, z_baro_top] [, z_baro_bottom])[0]

#  z_hpa is Sea Level Adjusted (Relative) barometer in hPa or mB
#  z_month is current month as a number between 1 to 12
#  z_wind is integer 0 to 11. 0 = N, 1 = NNE, 2 = NE, ... , 15 = NNW
#  NB. if calm a 'nonsense' value should be sent as z_wind (direction) eg. None
#  z_trend is barometer trend: 0 = no change, 1= rise, 2 = fall
#  z_north - in northern hemisphere, default True
#  z_baro_top - upper range of barometer, default 1050
#  z_baro_bottom - lower range of barometer, default 950
#  [0] a short forecast text is returned
#  [1] zambretti result_code number (0 - 25) is returned ie. Zambretti() returns a two deep array

def _(msg) : return msg

z_forecast = [
    _("Settled fine"), _("Fine weather"), _("Becoming fine"),
    _("Fine, becoming less settled"), _("Fine, possible showers"),
    _("Fairly fine, improving"), _("Fairly fine, possible showers early"),
    _("Fairly fine, showery later"), _("Showery early, improving"),
    _("Changeable, mending"), _("Fairly fine, showers likely"),
    _("Rather unsettled clearing later"), _("Unsettled, probably improving"),
    _("Showery, bright intervals"), _("Showery, becoming less settled"),
    _("Changeable, some rain"), _("Unsettled, short fine intervals"),
    _("Unsettled, rain later"), _("Unsettled, some rain"),
    _("Mostly very unsettled"), _("Occasional rain, worsening"),
    _("Rain at times, very unsettled"), _("Rain at frequent intervals"),
    _("Rain, very unsettled"), _("Stormy, may improve"), _("Stormy, much rain")
    ]

del _

# equivalents of Zambretti 'dial window' letters A - Z
rise_options   = [25,25,25,24,24,19,16,12,11, 9, 8, 6, 5, 2,1,1,0,0,0,0,0,0]
steady_options = [25,25,25,25,25,25,23,23,22,18,15,13,10, 4,1,1,0,0,0,0,0,0]
fall_options   = [25,25,25,25,25,25,25,25,23,23,21,20,17,14,7,3,1,1,1,0,0,0]

wind_scale = [6.0, 5.0, 5.0, 2.0, -0.5, -2.0, -5.0, -8.5,
              -12.0, -10.0, -6.0, -4.5, -3.0, -0.5, 1.5, 3.0]

def Zambretti(z_hpa, z_month, z_wind, z_trend,
               z_north=True, z_baro_top=1050.0, z_baro_bottom=950.0):
    z_option = (z_hpa - z_baro_bottom) / (z_baro_top - z_baro_bottom)
    if isinstance(z_wind, int) and z_wind >= 0 and z_wind < 16:
        if not z_north:
            # southern hemisphere, so add 180 degrees
            z_wind = (z_wind + 8) % 16
        z_option += wind_scale[z_wind] / 100.0
    if z_north == (z_month >= 4 and z_month <= 9):
        # local summer
        if z_trend == 1:
            z_option += 7.0 / 100.0
        elif z_trend == 2:
            z_option -= 7.0 / 100.0

    z_option = int(math.floor(z_option * 22.0))
    result_text = ""
    if(z_option < 0):
        z_option = 0
        result_text = "Exceptional Weather: "
    elif(z_option > 21):
        z_option = 21
        result_text = "Exceptional Weather: "

    if z_trend == 1:
        result_code = rise_options[z_option]
    elif z_trend == 2:
        result_code = fall_options[z_option]
    else:
        result_code = steady_options[z_option]
    result_text += z_forecast[result_code]
    return result_text, result_code

if __name__ == "__main__":
    print Zambretti(965, 7, 8, -0.5)
    print Zambretti(1000.5, 7, 8, -0.5)
    print Zambretti(1000.5, 7, 8, +0.5)
