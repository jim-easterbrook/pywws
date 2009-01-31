#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

"""
Plot graphs of temperature, wind speed, rainfall & pressure over the
last 24 hours.

usage: python Plot_24Hrs.py [options] data_dir temp_dir output_file
options are:
\t-h or --help\t\tdisplay this help
data_dir is the root directory of the weather data
temp_dir is a workspace for temporary files e.g. /tmp
output_file is the name of the image file to be created e.g. 24hrs.png
"""

from datetime import datetime, timedelta
import getopt
import os
import sys

import DataStore
from WeatherStation import dew_point

def Plot_24Hrs(params, raw_data, hourly_data, work_dir, output_file):
    pressure_offset = eval(params.get('fixed', 'pressure offset'))
    # set start of graph to 24 hours before last data item
    x_lo = raw_data.before(datetime.max)
    if x_lo == None:
        print >>sys.stderr, "No data - run LogData.py or EWtoPy.py first"
        return 4
    x_lo = x_lo + timedelta(minutes=55)
    x_lo = x_lo.replace(minute=0, second=0) - timedelta(hours=24)
    x_hi = x_lo + timedelta(hours=24)
    # open temporary data files
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    temp_file = os.path.join(work_dir, 'plot_24_temp.dat')
    wind_file = os.path.join(work_dir, 'plot_24_wind.dat')
    pressure_file = os.path.join(work_dir, 'plot_24_pressure.dat')
    rain_file = os.path.join(work_dir, 'plot_24_rain.dat')
    temp = open(temp_file, 'w')
    wind = open(wind_file, 'w')
    pressure = open(pressure_file, 'w')
    rain = open(rain_file, 'w')
    # iterate over hours, starting and ending off edge of graph
    got_rain = False
    start = x_lo - timedelta(hours=1)
    for hour in range(26):
        stop = start + timedelta(hours=1)
        for data in raw_data[start:stop]:
            if data['temp_out'] != None and data['hum_out'] != None:
                temp.write('%s %.1f %.2f\n' % (
                    data['idx'].isoformat(), data['temp_out'],
                    dew_point(data['temp_out'], data['hum_out'])))
            if data['wind_ave'] != None and data['wind_gust'] != None:
                wind.write('%s %.2f %.2f\n' % (
                    data['idx'].isoformat(),
                    data['wind_ave'] * 3.6 / 1.609344,
                    data['wind_gust'] * 3.6 / 1.609344))
            pressure.write('%s %.1f\n' % (
                data['idx'].isoformat(), data['pressure'] + pressure_offset))
        for data in hourly_data[start:stop]:
            # output rain data
            centre = start + timedelta(minutes=30)
            rain.write('%s %.1f\n' % (centre.isoformat(), data['rain']))
            got_rain = True
        start = stop
    temp.close()
    wind.close()
    pressure.close()
    rain.close()
    # write gnuplot command file
    cmd_file = os.path.join(work_dir, 'plot_24.cmd')
    of = open(cmd_file, 'w')
    of.write('set terminal png large size 600,800\n')
    of.write('set output "%s"\n' % output_file)
    of.write('set xdata time\n')
    of.write('set timefmt "%Y-%m-%dT%H:%M:%S"\n')
    of.write('set xrange ["%s":"%s"]\n' % (x_lo.isoformat(), x_hi.isoformat()))
    of.write('set xtics 7200\n')
    of.write('set lmargin 3\n')
    of.write('set bmargin 0.9\n')
    of.write('set multiplot layout 4,1\n')
    of.write('set format x "%H%M"\n')
    # plot temperature
    lo, hi = eval(params.get('plot range', 'temp', '-5, 30'))
    of.write('set yrange [%d:%d]\n' % (lo, hi))
    of.write('plot "%s" using 1:2 title "Temperature (°C)" smooth unique, \\\n' % temp_file)
    of.write('     "%s" using 1:3 title "Dew point (°C)" smooth unique lc 3\n' % temp_file)
    # plot wind
    lo, hi = eval(params.get('plot range', 'wind', '0, 25'))
    of.write('set yrange [%d:%d]\n' % (lo, hi))
    of.write('plot "%s" using 1:3 title "Wind speed: gust (mph)" smooth unique lc 4, \\\n' % wind_file)
    of.write('     "%s" using 1:2 title "average (mph)" smooth unique lc 3\n' % wind_file)
    # plot rain
    if got_rain:
        lo, hi = eval(params.get('plot range', 'rain hour', '0, 4'))
        of.write('set yrange [%d:%d]\n' % (lo, hi))
        of.write('set style fill solid\n')
        of.write('set boxwidth 2800\n')
        of.write('plot "%s" using 1:2 title "Hourly rainfall (mm)" lc 5 lw 0 with boxes\n' % rain_file)
    else:
        print >>sys.stderr, "No hourly summary data - run Process.py first"
    # label x axis of last plot
    of.write('set xlabel "Time(UTC)"\n')
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
    return Plot_24Hrs(DataStore.params(args[0]), DataStore.data_store(args[0]),
                      DataStore.hourly_store(args[0]), args[1], args[2])
if __name__ == "__main__":
    sys.exit(main())
