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

class GraphPlotter:
    def __init__(self, raw_data, hourly_data, daily_data, monthly_data, work_dir):
        self.raw_data = raw_data
        self.hourly_data = hourly_data
        self.daily_data = daily_data
        self.monthly_data = monthly_data
        self.work_dir = work_dir
        # create work directory
        if not os.path.isdir(self.work_dir):
            os.makedirs(self.work_dir)
    def DoPlot(self, input_file, output_file):
        # read XML graph description
        self.doc = xml.dom.minidom.parse(input_file)
        self.graph = self.doc.childNodes[0]
        # get list of plots
        plot_list = self.GetPlotList()
        self.plot_count = len(plot_list)
        if self.plot_count < 1:
            # nothing to plot
            self.doc.unlink()
            return 1
        # get start and end datetimes
        self.x_lo = self.GetValue(self.graph, 'start', None)
        self.x_hi = self.GetValue(self.graph, 'stop', None)
        self.duration = self.GetValue(self.graph, 'duration', None)
        if self.duration == None:
            self.duration = timedelta(hours=24)
        else:
            self.duration = eval('timedelta(%s)' % self.duration)
        if self.x_lo != None:
            self.x_lo = eval('datetime(%s)' % self.x_lo)
            if self.x_hi != None:
                self.x_hi = eval('datetime(%s)' % self.x_hi)
                self.duration = self.x_hi - self.x_lo
            else:
                self.x_hi = self.x_lo + self.duration
        elif self.x_hi != None:
            self.x_hi = eval('datetime(%s)' % self.x_hi)
            self.x_lo = self.x_hi - self.duration
        else:
            self.x_hi = self.hourly_data.before(datetime.max)
            if self.x_hi == None:
                self.x_hi = datetime.utcnow()    # only if no hourly data
            # set end of graph to start of the next hour after last item
            self.x_hi = self.x_hi + timedelta(minutes=55)
            self.x_hi = self.x_hi.replace(minute=0, second=0)
            self.x_lo = self.x_hi - self.duration
            self.x_hi = self.x_hi + Local.utcoffset(self.x_lo)
            self.x_lo = self.x_hi - self.duration
        self.utcoffset = Local.utcoffset(self.x_lo)
        # open gnuplot command file
        self.tmp_files = []
        cmd_file = os.path.join(self.work_dir, 'plot.cmd')
        self.tmp_files.append(cmd_file)
        of = open(cmd_file, 'w')
        # write gnuplot set up
        self.rows = self.GetDefaultRows()
        self.cols = (self.plot_count + self.rows - 1) / self.rows
        self.rows, self.cols = eval(self.GetValue(
            self.graph, 'layout', '%d, %d' % (self.rows, self.cols)))
        w, h = self.GetDefaultPlotSize()
        w = w * self.cols
        h = h * self.rows
        w, h = eval(self.GetValue(self.graph, 'size', '(%d, %d)' % (w, h)))
        fileformat = self.GetValue(self.graph, 'fileformat', 'png')
        of.write('set terminal %s large size %d,%d\n' % (fileformat, w, h))
        of.write('set output "%s"\n' % output_file)
        # set overall title
        title = self.GetValue(self.graph, 'title', '')
        if title:
            title = codecs.encode(title, self.doc.encoding)
            title = 'title "%s"' % title
        of.write('set multiplot layout %d, %d %s\n' % (self.rows, self.cols, title))
        # do actual plots
        of.write(self.GetPreamble())
        for plot_no in range(self.plot_count):
            plot = plot_list[plot_no]
            # set key / title location
            title = self.GetValue(plot, 'title', '')
            title = codecs.encode(title, self.doc.encoding)
            of.write('set key horizontal title "%s"\n' % title)
            # set data source
            source = self.GetValue(plot, 'source', 'raw')
            if source == 'raw':
                source = self.raw_data
            elif source == 'hourly':
                source = self.hourly_data
            elif source == 'monthly':
                source = self.monthly_data
            else:
                source = self.daily_data
            # do the plot
            of.write(self.PlotData(plot_no, plot, source))
        of.close()
        self.doc.unlink()
        # run gnuplot on file
        os.system('gnuplot %s' % cmd_file)
        for file in self.tmp_files:
            os.unlink(file)
        return 0
    def GetChildren(self, node, name):
        result = []
        for child in node.childNodes:
            if child.localName == name:
                result.append(child)
        return result
    def GetValue(self, node, name, default):
        for child in node.childNodes:
            if child.localName == name:
                if child.childNodes:
                    return child.childNodes[0].data.strip()
                else:
                    return ''
        return default
    def GetPlotList(self):
        return self.GetChildren(self.graph, 'plot')
    def GetDefaultRows(self):
        return self.plot_count
    def GetDefaultPlotSize(self):
        return 200 / self.cols, 600 / self.cols
    def GetPreamble(self):
        result = """set style fill solid
set xdata time
set timefmt "%Y-%m-%dT%H:%M:%S"
set bmargin 0.9
"""
        result += 'set xrange ["%s":"%s"]\n' % (
            self.x_lo.isoformat(), self.x_hi.isoformat())
        lmargin = eval(self.GetValue(self.graph, 'lmargin', '5'))
        result += 'set lmargin %d\n' % (lmargin)
        if self.duration <= timedelta(hours=24):
            xformat = '%H%M'
        elif self.duration <= timedelta(days=7):
            xformat = '%a %d'
        else:
            xformat = '%Y/%m/%d'
        xformat = self.GetValue(self.graph, 'xformat', xformat)
        xformat = codecs.encode(xformat, self.doc.encoding)
        result += 'set format x "%s"\n' % xformat
        xtics = self.GetValue(self.graph, 'xtics', None)
        if xtics:
            result += 'set xtics %d\n' % (eval(xtics) * 3600)
        return result
    def PlotData(self, plot_no, plot, source):
        subplot_list = self.GetChildren(plot, 'subplot')
        subplot_count = len(subplot_list)
        if subplot_count < 1:
            return ''
        result = ''
        # label x axis of last plot
        if plot_no == self.plot_count - 1:
            result += 'set bmargin\n'
            if self.duration <= timedelta(hours=24):
                xlabel = 'Time (%Z)'
            elif self.duration <= timedelta(days=7):
                xlabel = 'Day'
            else:
                xlabel = 'Date'
            xlabel = self.GetValue(self.graph, 'xlabel', xlabel)
            xlabel = codecs.encode(xlabel, self.doc.encoding)
            result += 'set xlabel "%s"\n' % (
                self.x_lo.replace(tzinfo=Local).strftime(xlabel))
            dateformat = '%Y/%m/%d'
            dateformat = self.GetValue(self.graph, 'dateformat', dateformat)
            dateformat = codecs.encode(dateformat, self.doc.encoding)
            ldat = self.x_lo.replace(tzinfo=Local).strftime(dateformat)
            rdat = self.x_hi.replace(tzinfo=Local).strftime(dateformat)
            if ldat != '':
                result += 'set label "%s" at "%s", graph -0.3 left\n' % (
                    ldat, self.x_lo.isoformat())
            if rdat != ldat:
                result += 'set label "%s" at "%s", graph -0.3 right\n' % (
                    rdat, self.x_hi.isoformat())
        # set y range
        yrange = self.GetValue(plot, 'yrange', None)
        if yrange:
            result += 'set yrange [%d:%d]\n' % eval(yrange)
        else:
            result += 'set yrange [*:*]\n'
        # set grid
        result += 'unset grid\n'
        grid = self.GetValue(plot, 'grid', None)
        if grid != None:
            result += 'set grid %s\n' % grid
        # x_lo & x_hi are in local time, data is indexed in UTC
        start = self.x_lo - self.utcoffset
        stop = self.x_hi - self.utcoffset
        if source == self.raw_data:
            boxwidth = 240      # assume 5 minute data interval
            start = source.before(start)
        elif source == self.hourly_data:
            boxwidth = 2800
            start = source.before(start)
        elif source == self.monthly_data:
            boxwidth = 2800 * 24 * 30
        else:
            boxwidth = 2800 * 24
        boxwidth = eval(self.GetValue(plot, 'boxwidth', str(boxwidth)))
        result += 'set boxwidth %d\n' % boxwidth
        stop = source.after(stop)
        if stop:
            stop = stop + timedelta(minutes=1)
        result += 'plot '
        colour = 0
        for subplot_no in range(subplot_count):
            subplot = subplot_list[subplot_no]
            # write data file
            dat_file = os.path.join(self.work_dir, 'plot_%d_%d.dat' % (
                plot_no, subplot_no))
            self.tmp_files.append(dat_file)
            dat = open(dat_file, 'w')
            xcalc = self.GetValue(subplot, 'xcalc', "data['idx']")
            ycalc = self.GetValue(subplot, 'ycalc', None)
            xcalc = compile(xcalc, '<string>', 'eval')
            ycalc = compile(ycalc, '<string>', 'eval')
            for data in source[start:stop]:
                idx = eval(xcalc)
                if idx == None:
                    continue
                idx += self.utcoffset
                try:
                    value = eval(ycalc)
                except TypeError:
                    value = None
                if value != None:
                    dat.write('%s %g\n' % (idx.isoformat(), value))
            dat.close()
            # plot data
            style = self.GetValue(subplot, 'style', None)
            colour = eval(self.GetValue(subplot, 'colour', str(colour+1)))
            if style == 'box':
                style = 'lc %d lw 0 with boxes' % (colour)
            elif style == '+':
                style = 'lc %d pt 1 with points' % (colour)
            elif style == 'x':
                style = 'lc %d pt 2 with points' % (colour)
            else:
                style = 'smooth unique lc %d' % (colour)
            title = self.GetValue(subplot, 'title', '')
            title = codecs.encode(title, self.doc.encoding)
            result += ' "%s" using 1:2 title "%s" %s' % (dat_file, title, style)
            if subplot_no != subplot_count - 1:
                result += ', \\'
            result += '\n'
        return result
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
    return GraphPlotter(
        DataStore.data_store(args[0]), DataStore.hourly_store(args[0]),
        DataStore.daily_store(args[0]), DataStore.monthly_store(args[0]),
        args[1]
        ).DoPlot(args[2], args[3])
if __name__ == "__main__":
    sys.exit(main())
