#!/usr/bin/env python

"""
Plot a "wind rose".

usage: python WindRose.py [options] data_dir temp_dir xml_file output_file
options are:
\t-h or --help\t\tdisplay this help
data_dir is the root directory of the weather data
temp_dir is a workspace for temporary files e.g. /tmp
xml_file is the name of the source file that describes the plot
output_file is the name of the image file to be created e.g. 24hrs.png
"""

import codecs
from collections import defaultdict
from datetime import datetime, timedelta
import getopt
import os
import sys
import xml.dom.minidom

import DataStore
from TimeZone import Local
from WeatherStation import dew_point

def GetValue(node, name, default):
    result = node.getElementsByTagName(name)
    if len(result) < 1:
        return default
    result = result[0].childNodes
    if len(result) < 1:
        return ''
    return result[0].data.strip()
def WindRose(params, raw_data, hourly_data, daily_data, monthly_data,
             work_dir, input_file, output_file):
    pressure_offset = eval(params.get('fixed', 'pressure offset'))
    # create work directory
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    tmp_files = []
    # read XML graph description
    graph = xml.dom.minidom.parse(input_file)
    # get start and end datetimes
    x_lo = GetValue(graph, 'start', None)
    x_hi = GetValue(graph, 'stop', None)
    duration = GetValue(graph, 'duration', None)
    if duration == None:
        duration = timedelta(hours=24)
    else:
        duration = eval('timedelta(%s)' % duration)
    if x_lo != None:
        x_lo = eval('datetime(%s)' % x_lo)
        if x_hi != None:
            x_hi = eval('datetime(%s)' % x_hi)
            duration = x_hi - x_lo
        else:
            x_hi = x_lo + duration
    elif x_hi != None:
        x_hi = eval('datetime(%s)' % x_hi)
        x_lo = x_hi - duration
    else:
        x_hi = hourly_data.before(datetime.max)
        if x_hi == None:
            x_hi = datetime.utcnow()    # only if no hourly data
        # set end of graph to start of the next hour after last item
        x_hi = x_hi + timedelta(minutes=55)
        x_hi = x_hi.replace(minute=0, second=0)
        x_lo = x_hi - duration
        x_hi = x_hi + Local.utcoffset(x_lo)
        x_lo = x_hi - duration
    utcoffset = Local.utcoffset(x_lo)
    # open gnuplot command file
    cmd_file = os.path.join(work_dir, 'windrose.cmd')
    tmp_files.append(cmd_file)
    of = open(cmd_file, 'w')
    # write gnuplot set up
    size = eval(GetValue(graph, 'size', '(600, 600)'))
    of.write('set terminal png large size %d,%d\n' % size)
    of.write('set output "%s"\n' % output_file)
    of.write('set polar\n')
    of.write('set angles degrees\n')
    of.write('set grid polar 22.5\n')
    of.write('set xtics axis nomirror\n')
    of.write('set ytics axis nomirror\n')
    of.write('set xrange [-15:15]\n')
    of.write('set yrange [-15:15]\n')
    of.write('set zeroaxis\n')
    # do the plot
    source = GetValue(graph, 'source', 'raw')
    # x_lo & x_hi are in local time, data is indexed in UTC
    start = x_lo - utcoffset
    stop = x_hi - utcoffset
    if source == 'raw':
        source = raw_data
        start = source.before(start)
    elif source == 'hourly':
        source = hourly_data
        start = source.before(start)
    elif source == 'monthly':
        source = monthly_data
    else:
        source = daily_data
    stop = source.after(stop)
    if stop:
        stop = stop + timedelta(minutes=1)
    # get statistics
    thresh = (0.0, 1.54, 3.09, 5.14, 8.23, 10.8, 15.5, 999.0)
    histograms = []
    for i in range(len(thresh)):
        hist = []
        for n in range(16):
            hist.append(0)
        histograms.append(hist)
    for data in source[start:stop]:
        if data['wind_dir'] == None:
            continue
        for t in range(len(thresh)):
            if data['wind_ave'] <= thresh[t]:
                histograms[t][data['wind_dir']] += 1
                break
    # evenly distribute zero speed
    total = 0
    for n in range(16):
        total += histograms[0][n]
    for n in range(16):
        histograms[0][n] = total / 16
    # integrate histograms
    for i in range(1, len(thresh)):
        for n in range(16):
            histograms[i][n] += histograms[i-1][n]
    total = 0
    for n in range(16):
        total += histograms[-1][n]
    of.write('plot ')
    # plot segments for each speed-direction
    title = GetValue(graph, 'title', '')
    title = codecs.encode(title, graph.encoding)
    for i in range(len(thresh)-1, -1, -1):
        dat_file = os.path.join(work_dir, 'windrose_%d.dat' % i)
        tmp_files.append(dat_file)
        dat = open(dat_file, 'w')
        sub_total = 0
        for n in range(16):
            angle = 90.0 - (n * 22.5)
            sub_total += histograms[i][n]
            value = 100.0 * float(histograms[i][n]) / float(total)
            if i == 0:
                dat.write('%g %g\n' % (angle - 11.24, value * 0.994))
            else:
                dat.write('%g %g\n' % (angle - 8.1, 0))
            dat.write('%g %g\n' % (angle - 8.0, value * 0.997))
            dat.write('%g %g\n' % (angle, value))
            dat.write('%g %g\n' % (angle + 8.0, value * 0.997))
            if i == 0:
                dat.write('%g %g\n' % (angle + 11.24, value * 0.994))
                dat.write('%g %g\n' % (angle + 11.25, 0))
            else:
                dat.write('%g %g\n' % (angle + 8.1, 0))
        dat.close()
        # plot data
        value = 100.0 * float(sub_total) / float(total)
        of.write('"%s" using 1:2 title "wind <= %g m/s (%.3g%%)" with filledcurve lt %d' % (
            dat_file, thresh[i], value, i))
        if i > 0:
            of.write(', \\')
        of.write('\n')
    dat.close()
    of.close()
    graph.unlink()
    # run gnuplot on file
    os.system('gnuplot %s' % cmd_file)
    for file in tmp_files:
        os.unlink(file)
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
    # process options
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
    # check arguments
    if len(args) != 4:
        print >>sys.stderr, 'Error: 4 arguments required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    return WindRose(DataStore.params(args[0]), DataStore.data_store(args[0]),
                    DataStore.hourly_store(args[0]), DataStore.daily_store(args[0]),
                    DataStore.monthly_store(args[0]), args[1], args[2], args[3])
if __name__ == "__main__":
    sys.exit(main())
