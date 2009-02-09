#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

"""
Plot graphs of temperature, wind speed, rainfall & pressure over the
last 28 days.

usage: python Plot_28Days.py [options] data_dir temp_dir output_file
options are:
\t-h or --help\t\tdisplay this help
data_dir is the root directory of the weather data
temp_dir is a workspace for temporary files e.g. /tmp
output_file is the name of the image file to be created e.g. 28days.png
"""

from datetime import datetime, timedelta
import getopt
import os
import sys

import DataStore

def Plot_28Days(params, daily_data, hourly_data, work_dir, output_file):
    # set start of graph to 28 days before last data item
    x_hi = daily_data.before(datetime.max)
    if x_hi == None:
        print >>sys.stderr, "No daily summary data - run Process.py first"
        return 4
    x_hi = x_hi + timedelta(hours=3)    # ensure we get to right day
    x_hi = x_hi.replace(hour=21, minute=0, second=0)
    x_lo = x_hi - timedelta(days=28)
    # open temporary data files
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    tmax_file = os.path.join(work_dir, 'plot_28_tmax.dat')
    tmin_file = os.path.join(work_dir, 'plot_28_tmin.dat')
    wind_file = os.path.join(work_dir, 'plot_28_wind.dat')
    rain_file = os.path.join(work_dir, 'plot_28_rain.dat')
    pressure_file = os.path.join(work_dir, 'plot_28_pressure.dat')
    tmax = open(tmax_file, 'w')
    tmin = open(tmin_file, 'w')
    wind = open(wind_file, 'w')
    rain = open(rain_file, 'w')
    pressure = open(pressure_file, 'w')
    # iterate over data
    for data in daily_data[x_lo:]:
        centre = data['idx']
        if centre.hour >= 21:
            # got an incomplete record, so need to get to next day
            centre = centre + timedelta(hours=3)
        # centre rain on 9 am
        centre = centre.replace(hour=9, minute=0, second=0)
        rain.write('%s %.1f\n' % (centre.isoformat(), data['rain']))
        if data['temp_out_min'] != None:
            # centre nighttime min on 3 am
            centre = centre.replace(hour=3)
            tmin.write('%s %.1f\n' % (centre.isoformat(), data['temp_out_min']))
        if data['temp_out_max'] != None:
            # centre daytime max on 3 pm
            centre = centre.replace(hour=15)
            tmax.write('%s %.1f\n' % (centre.isoformat(), data['temp_out_max']))
    for data in hourly_data[x_lo:]:
        if data['wind_ave'] != None and data['wind_gust'] != None:
            wind.write('%s %.2f %.2f\n' % (
                data['idx'].isoformat(),
                data['wind_ave'] * 3.6 / 1.609344,
                data['wind_gust'] * 3.6 / 1.609344))
        pressure.write('%s %.1f\n' % (
            data['idx'].isoformat(), data['pressure']))
    tmax.close()
    tmin.close()
    wind.close()
    rain.close()
    pressure.close()
    # write gnuplot command file
    cmd_file = os.path.join(work_dir, 'plot_28.cmd')
    of = open(cmd_file, 'w')
    of.write('set terminal png large size 600,800\n')
    of.write('set output "%s"\n' % output_file)
    of.write('set xdata time\n')
    of.write('set timefmt "%Y-%m-%dT%H:%M:%S"\n')
    of.write('set xrange ["%s":"%s"]\n' % (x_lo.isoformat(), x_hi.isoformat()))
    of.write('set lmargin 3\n')
    of.write('set bmargin 0.9\n')
    of.write('set multiplot layout 4,1\n')
    of.write('set format x "%d/%m"\n')
    # plot temperature
    lo, hi = eval(params.get('plot range', 'temp', '-5, 30'))
    of.write('set yrange [%d:%d]\n' % (lo, hi))
    of.write('set style fill solid\n')
    of.write('set boxwidth %d\n' % (2800 * 12))
    of.write('plot "%s" using 1:2 title "Daytime max. temp (°C)" lc 1 lw 0 with boxes, \\\n' % tmax_file)
    of.write('     "%s" using 1:2 title "Nighttime min. temp (°C)" lc 3 lw 0 with boxes\n' % tmin_file)
#    of.write('plot "%s" using 1:2 title "Max. temp (°C)" lc 1 pt 1, \\\n' % tmax_file)
#    of.write('     "%s" using 1:2 title "Min. temp (°C)" lc 3 pt 1\n' % tmin_file)
    # plot wind
    lo, hi = eval(params.get('plot range', 'wind', '0, 25'))
    of.write('set yrange [%d:%d]\n' % (lo, hi))
    of.write('plot "%s" using 1:3 title "Wind speed: gust (mph)" smooth unique lc 4, \\\n' % wind_file)
    of.write('     "%s" using 1:2 title "average (mph)" smooth unique lc 3\n' % wind_file)
    # plot rain
    lo, hi = eval(params.get('plot range', 'rain 6-hour', '0, 16'))
    of.write('set yrange [%d:%d]\n' % (lo, hi * 2))
    of.write('set style fill solid\n')
    of.write('set boxwidth %d\n' % (2800 * 24))
    of.write('plot "%s" using 1:2 title "Daily rainfall (mm)" lc 5 lw 0 with boxes\n' % rain_file)
    # label x axis of last plot
    of.write('set xlabel "Date"\n')
    of.write('set bmargin\n')
    # plot pressure
    lo, hi = eval(params.get('plot range', 'pressure', '980, 1050'))
    of.write('set yrange [%d:%d]\n' % (lo, hi))
    of.write('plot "%s" using 1:2 title "Pressure (hPa)" smooth unique lc 2\n' % pressure_file)
    of.close()
    # run gnuplot on file
    os.system('gnuplot %s' % cmd_file)
    return 0
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # check arguments
    if len(args) != 3:
        print >>sys.stderr, 'Error: 3 arguments required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    # process options
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
    return Plot_28Days(DataStore.params(args[0]), DataStore.daily_store(args[0]),
                      DataStore.hourly_store(args[0]), args[1], args[2])
if __name__ == "__main__":
    sys.exit(main())
