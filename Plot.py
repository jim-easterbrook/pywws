#!/usr/bin/env python

"""
Plot graphs of weather data according to an XML recipe.

usage: python Plot.py [options] data_dir temp_dir xml_file output_file
options are:
\t-h or --help\t\tdisplay this help
data_dir is the root directory of the weather data
temp_dir is a workspace for temporary files e.g. /tmp
xml_file is the name of the source file that describes the plot
output_file is the name of the image file to be created e.g. 24hrs.png
"""

import codecs
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
def Plot(params, raw_data, hourly_data, daily_data, work_dir, input_file, output_file):
    pressure_offset = eval(params.get('fixed', 'pressure offset'))
    # create work directory
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    # read XML graph description
    graph = xml.dom.minidom.parse(input_file)
    # get start and end of graph
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
    cmd_file = os.path.join(work_dir, 'plot.cmd')
    of = open(cmd_file, 'w')
    # get list of plots
    plot_list = graph.getElementsByTagName('plot')
    plot_count = len(plot_list)
    # write gnuplot set up
    size = eval(GetValue(graph, 'size', '(600, %d)' % (plot_count * 200)))
    of.write('set terminal png large size %d,%d\n' % size)
    of.write('set output "%s"\n' % output_file)
    of.write('set style fill solid\n')
    of.write('set xdata time\n')
    of.write('set timefmt "%Y-%m-%dT%H:%M:%S"\n')
    of.write('set xrange ["%s":"%s"]\n' % (x_lo.isoformat(), x_hi.isoformat()))
    of.write('set lmargin 3\n')
    of.write('set bmargin 0.9\n')
    if duration <= timedelta(hours=24):
        xformat = '%H%M'
        xlabel = 'Time (%Z)'
    elif duration <= timedelta(days=7):
        xformat = '%a %d'
        xlabel = 'Day'
    else:
        xformat = '%Y/%m/%d'
        xlabel = 'Date'
    xformat = GetValue(graph, 'xformat', xformat)
    xformat = codecs.encode(xformat, graph.encoding)
    of.write('set format x "%s"\n' % xformat)
    xlabel = GetValue(graph, 'xlabel', xlabel)
    xlabel = codecs.encode(xlabel, graph.encoding)
    dateformat = '%Y/%m/%d'
    dateformat = GetValue(graph, 'dateformat', dateformat)
    dateformat = codecs.encode(dateformat, graph.encoding)
    xtics = GetValue(graph, 'xtics', None)
    if xtics:
        of.write('set xtics %d\n' % (eval(xtics) * 3600))
    # do the plots
    of.write('set multiplot layout %d,1\n' % plot_count)
    colour = 0
    for plot_no in range(plot_count):
        plot = plot_list[plot_no]
        subplot_list = plot.getElementsByTagName('subplot')
        subplot_count = len(subplot_list)
        if subplot_count < 1:
            continue
        # label x axis of last plot
        if plot_no == plot_count - 1:
            of.write('set bmargin\n')
            of.write('set xlabel "%s"\n' % (
                x_lo.replace(tzinfo=Local).strftime(xlabel)))
            ldat = x_lo.replace(tzinfo=Local).strftime(dateformat)
            rdat = x_hi.replace(tzinfo=Local).strftime(dateformat)
            if ldat != '':
                of.write('set label "%s" at "%s", graph -0.3 left\n' % (
                    ldat, x_lo.isoformat()))
            if rdat != ldat:
                of.write('set label "%s" at "%s", graph -0.3 right\n' % (
                    rdat, x_hi.isoformat()))
        # set y range
        yrange = GetValue(plot, 'yrange', None)
        if yrange:
            of.write('set yrange [%d:%d]\n' % eval(yrange))
        else:
            of.write('set yrange [*:*]\n')
        # set grid
        of.write('unset grid\n')
        grid = GetValue(plot, 'grid', None)
        if grid != None:
            of.write('set grid %s\n' % grid)
        source = GetValue(plot, 'source', 'raw')
        # x_lo & x_hi are in local time, data is indexed in UTC
        start = x_lo - utcoffset
        stop = x_hi - utcoffset
        if source == 'raw':
            source = raw_data
            boxwidth = 240      # assume 5 minute data interval
            start = source.before(start)
        elif source == 'hourly':
            source = hourly_data
            boxwidth = 2800
            start = source.before(start)
        else:
            source = daily_data
            boxwidth = 2800 * 24
        stop = source.after(stop)
        if stop:
            stop = stop + timedelta(minutes=1)
        boxwidth = eval(GetValue(plot, 'boxwidth', str(boxwidth)))
        of.write('set boxwidth %d\n' % boxwidth)
        of.write('plot ')
        for subplot_no in range(subplot_count):
            subplot = subplot_list[subplot_no]
            # write data file
            dat_file = os.path.join(work_dir, 'plot_%d_%d.dat' % (
                plot_no, subplot_no))
            dat = open(dat_file, 'w')
            xcalc = GetValue(subplot, 'xcalc', "data['idx']")
            ycalc = GetValue(subplot, 'ycalc', None)
            xcalc = compile(xcalc, '<string>', 'eval')
            ycalc = compile(ycalc, '<string>', 'eval')
            for data in source[start:stop]:
                idx = eval(xcalc) + utcoffset
                value = eval(ycalc)
                if value != None:
                    dat.write('%s %g\n' % (idx.isoformat(), value))
            dat.close()
            # plot data
            style = GetValue(subplot, 'style', None)
            colour = eval(GetValue(subplot, 'colour', str(colour+1)))
            if style == 'box':
                style = 'lc %d lw 0 with boxes' % (colour)
            else:
                style = 'smooth unique lc %d' % (colour)
            title = GetValue(subplot, 'title', '')
            title = codecs.encode(title, graph.encoding)
            of.write(' "%s" using 1:2 title "%s" %s' % (dat_file, title, style))
            if subplot_no != subplot_count - 1:
                of.write(', \\')
            of.write('\n')
    of.close()
    graph.unlink()
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
    return Plot(DataStore.params(args[0]), DataStore.data_store(args[0]),
                DataStore.hourly_store(args[0]), DataStore.daily_store(args[0]),
                args[1], args[2], args[3])
if __name__ == "__main__":
    sys.exit(main())
