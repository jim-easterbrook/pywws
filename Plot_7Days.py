#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

from datetime import date, datetime, timedelta
import getopt
import os
import sys

import DataStore
from WeatherStation import dew_point

def Plot_7Days(params, hourly_data, work_dir, output_file):
    # set start of graph to 28 quarter-days before last record
    x_lo = hourly_data.before(datetime.max)
    if x_lo == None:
        print >>sys.stderr, "No hourly summary data - run Process.py first"
        return 4
    x_lo = x_lo + timedelta(hours=5, minutes=55)
    x_lo = x_lo.replace(minute=0, second=0) - timedelta(hours=x_lo.hour % 6)
    x_lo = x_lo - timedelta(days=7)
    # open temporary data files
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    temp_file = os.path.join(work_dir, 'plot_7_temp.dat')
    wind_file = os.path.join(work_dir, 'plot_7_wind.dat')
    rain_file = os.path.join(work_dir, 'plot_7_rain.dat')
    pressure_file = os.path.join(work_dir, 'plot_7_pressure.dat')
    temp = open(temp_file, 'w')
    wind = open(wind_file, 'w')
    rain = open(rain_file, 'w')
    pressure = open(pressure_file, 'w')
    # iterate over 6-hour chunks, starting off edge of graph
    start = x_lo - timedelta(hours=6)
    for quarter in range(29):
        rain_total = 0.0
        stop = start + timedelta(hours=6)
        for data in hourly_data[start:stop]:
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
                data['idx'].isoformat(), data['pressure']))
            rain_total += data['rain']
        # output rain data
        centre = start + timedelta(hours=3)
        rain.write('%s %.1f\n' % (centre.isoformat(), rain_total))
        start = stop
    temp.close()
    wind.close()
    rain.close()
    pressure.close()
    # write gnuplot command file
    cmd_file = os.path.join(work_dir, 'plot_7.cmd')
    of = open(cmd_file, 'w')
    of.write('set terminal png large size 600,800\n')
    of.write('set output "%s"\n' % output_file)
    of.write('set xdata time\n')
    of.write('set timefmt "%Y-%m-%dT%H:%M:%S"\n')
    of.write('set xrange ["%s":"%s"]\n' % (x_lo.isoformat(), stop.isoformat()))
    of.write('set xtics offset 4.3,0 %d\n' % (3600 * 24))
    of.write('set lmargin 3\n')
    of.write('set bmargin 0.9\n')
    of.write('set multiplot layout 4,1\n')
    of.write('set format x "%a %d"\n')
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
    lo, hi = eval(params.get('plot range', 'rain 6-hour', '0, 16'))
    of.write('set yrange [%d:%d]\n' % (lo, hi))
    of.write('set style fill solid\n')
    of.write('set boxwidth %d\n' % (2800 * 6))
    of.write('plot "%s" using 1:2 title "6-hourly rainfall (mm)" lc 5 lw 0 with boxes\n' % rain_file)
    # label x axis of last plot
    of.write('set xlabel "Day"\n')
    of.write('set bmargin\n')
    # plot pressure
    lo, hi = eval(params.get('plot range', 'pressure', '980, 1050'))
    of.write('set yrange [%d:%d]\n' % (lo, hi))
    of.write('plot "%s" using 1:2 title "Pressure (hPa)" smooth unique lc 2\n' % pressure_file)
    of.close()
    # run gnuplot on file
    os.system('gnuplot %s' % cmd_file)
    return 0
def usage():
    print >>sys.stderr, 'usage: %s [options] data_directory temp_directory output_file' % sys.argv[0]
    print >>sys.stderr, '''\toptions are:
    \t--help\t\t\tdisplay this help'''
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, msg
        usage()
        return 1
    # process options
    for o, a in opts:
        if o == '--help':
            usage()
            return 0
    # process arguments
    if len(args) != 3:
        print >>sys.stderr, "3 arguments required"
        usage()
        return 2
    return Plot_7Days(DataStore.params(args[0]), DataStore.hourly_store(args[0]),
                      args[1], args[2])
if __name__ == "__main__":
    sys.exit(main())
