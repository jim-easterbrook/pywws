#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Plot graphs of weather data according to an XML recipe
::

%s

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.Plot [options] data_dir temp_dir xml_file output_file
 options are:
  -h or --help    display this help
 data_dir is the root directory of the weather data
 temp_dir is a workspace for temporary files e.g. /tmp
 xml_file is the name of the source file that describes the plot
 output_file is the name of the image file to be created e.g. 24hrs.png
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import codecs
from datetime import datetime, timedelta
import getopt
import os
import subprocess
import sys
import xml.dom.minidom

from .conversions import (
    illuminance_wm2, pressure_inhg, rain_inch, temp_f,
    winddir_degrees, winddir_text, wind_kmph, wind_mph, wind_kn, wind_bft,
    cadhumidex)
from . import DataStore
from . import Localisation
from .TimeZone import Local
from .WeatherStation import dew_point, wind_chill, apparent_temp

class BasePlotter(object):
    def __init__(self, params, status, raw_data, hourly_data,
                 daily_data, monthly_data, work_dir):
        self.raw_data = raw_data
        self.hourly_data = hourly_data
        self.daily_data = daily_data
        self.monthly_data = monthly_data
        self.work_dir = work_dir
        self.pressure_offset = eval(status.get('fixed', 'pressure offset'))
        # set language related stuff
        self.encoding = params.get('config', 'gnuplot encoding', 'iso_8859_1')
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
        if sys.version_info[0] >= 3:
            of = open(cmd_file, 'w', encoding=self.encoding)
        else:
            of = open(cmd_file, 'w')
        # write gnuplot set up
        self.rows = self.GetDefaultRows()
        self.cols = (self.plot_count + self.rows - 1) // self.rows
        self.rows, self.cols = eval(self.GetValue(
            self.graph, 'layout', '%d, %d' % (self.rows, self.cols)))
        w, h = self.GetDefaultPlotSize()
        w = w * self.cols
        h = h * self.rows
        w, h = eval(self.GetValue(self.graph, 'size', '(%d, %d)' % (w, h)))
        fileformat = self.GetValue(self.graph, 'fileformat', 'png')
        if fileformat == 'svg':
            terminal = '%s enhanced font "arial,9" size %d,%d dynamic rounded' % (
                fileformat, w, h)
        else:
            terminal = '%s large size %d,%d' % (fileformat, w, h)
        terminal = self.GetValue(self.graph, 'terminal', terminal)
        of.write('set encoding %s\n' % (self.encoding))
        of.write('set terminal %s\n' % (terminal))
        of.write('set output "%s"\n' % (output_file))
        # set overall title
        title = self.GetValue(self.graph, 'title', '')
        if title:
            if sys.version_info[0] < 3:
                title = title.encode(self.encoding)
            title = 'title "%s"' % title
        of.write('set multiplot layout %d, %d %s\n' % (self.rows, self.cols, title))
        # do actual plots
        of.write(self.GetPreamble())
        for plot_no in range(self.plot_count):
            plot = plot_list[plot_no]
            # set key / title location
            title = self.GetValue(plot, 'title', '')
            if sys.version_info[0] < 3:
                title = title.encode(self.encoding)
            of.write('set key horizontal title "%s"\n' % title)
            # optional yaxis labels
            ylabel = self.GetValue(plot, 'ylabel', '')
            if ylabel:
                if sys.version_info[0] < 3:
                    ylabel = ylabel.encode(self.encoding)
                ylabelangle = self.GetValue(plot, 'ylabelangle', '')
                if ylabelangle:
                    ylabelangle = ' rotate by %s' % (ylabelangle)
                of.write('set ylabel "%s"%s\n' % (ylabel, ylabelangle))
            else:
                of.write('set ylabel\n')
            y2label = self.GetValue(plot, 'y2label', '')
            if y2label:
                if sys.version_info[0] < 3:
                    y2label = y2label.encode(self.encoding)
                y2labelangle = self.GetValue(plot, 'y2labelangle', '')
                if y2labelangle:
                    y2labelangle = ' rotate by %s' % (y2labelangle)
                of.write('set y2label "%s"%s\n' % (y2label, y2labelangle))
            else:
                of.write('set y2label\n')
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
        subprocess.check_call(['gnuplot', cmd_file])
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

class Record(object):
    pass

class GraphPlotter(BasePlotter):
    def GetPlotList(self):
        return self.GetChildren(self.graph, 'plot')

    def GetDefaultRows(self):
        return self.plot_count

    def GetDefaultPlotSize(self):
        return 200 // self.cols, 600 // self.cols

    def GetPreamble(self):
        result = """set style fill solid
set xdata time
set timefmt "%Y-%m-%dT%H:%M:%S"
"""
        result += 'set xrange ["%s":"%s"]\n' % (
            self.x_lo.isoformat(), self.x_hi.isoformat())
        lmargin = eval(self.GetValue(self.graph, 'lmargin', '5'))
        result += 'set lmargin %g\n' % (lmargin)
        rmargin = eval(self.GetValue(self.graph, 'rmargin', '-1'))
        result += 'set rmargin %g\n' % (rmargin)
        if self.duration <= timedelta(hours=24):
            xformat = '%H%M'
        elif self.duration <= timedelta(days=7):
            xformat = '%a %d'
        else:
            xformat = '%Y/%m/%d'
        xformat = self.GetValue(self.graph, 'xformat', xformat)
        result += 'set format x "%s"\n' % xformat
        xtics = self.GetValue(self.graph, 'xtics', None)
        if xtics:
            result += 'set xtics %d\n' % (eval(xtics) * 3600)
        if sys.version_info[0] < 3:
            result = result.encode(self.encoding)
        return result

    def PlotData(self, plot_no, plot, source):
        _ = Localisation.translation.ugettext
        subplot_list = self.GetChildren(plot, 'subplot')
        subplot_count = len(subplot_list)
        if subplot_count < 1:
            return ''
        result = ''
        pressure_offset = self.pressure_offset
        # label x axis of last plot
        if plot_no == self.plot_count - 1:
            if self.duration <= timedelta(hours=24):
                xlabel = _('Time (%Z)')
            elif self.duration <= timedelta(days=7):
                xlabel = _('Day')
            else:
                xlabel = _('Date')
            xlabel = self.GetValue(self.graph, 'xlabel', xlabel)
            if sys.version_info[0] < 3:
                xlabel = xlabel.encode(self.encoding)
            result += 'set xlabel "%s"\n' % (
                self.x_lo.replace(tzinfo=Local).strftime(xlabel))
            dateformat = '%Y/%m/%d'
            dateformat = self.GetValue(self.graph, 'dateformat', dateformat)
            if sys.version_info[0] < 3:
                dateformat = dateformat.encode(self.encoding)
            ldat = self.x_lo.replace(tzinfo=Local).strftime(dateformat)
            rdat = self.x_hi.replace(tzinfo=Local).strftime(dateformat)
            if ldat != '':
                result += 'set label "%s" at "%s", graph -0.3 left\n' % (
                    ldat, self.x_lo.isoformat())
            if rdat != ldat:
                result += 'set label "%s" at "%s", graph -0.3 right\n' % (
                    rdat, self.x_hi.isoformat())
        # set bottom margin
        bmargin = eval(self.GetValue(plot, 'bmargin', '-1'))
        result += 'set bmargin %g\n' % (bmargin)
        # set y ranges and tics
        yrange = self.GetValue(plot, 'yrange', None)
        y2range = self.GetValue(plot, 'y2range', None)
        ytics = self.GetValue(plot, 'ytics', 'autofreq')
        y2tics = self.GetValue(plot, 'y2tics', '')
        if y2tics and not y2range:
            y2range = yrange
        elif y2range and not y2tics:
            y2tics = 'autofreq'
        if yrange:
            result += 'set yrange [%s]\n' % (yrange.replace(',', ':'))
        else:
            result += 'set yrange [*:*]\n'
        if y2range:
            result += 'set y2range [%s]\n' % (y2range.replace(',', ':'))
        if y2tics:
            result += 'set ytics nomirror %s; set y2tics %s\n' % (ytics, y2tics)
        else:
            result += 'unset y2tics; set ytics mirror %s\n' % (ytics)
        # set grid
        result += 'unset grid\n'
        grid = self.GetValue(plot, 'grid', None)
        if grid != None:
            result += 'set grid %s\n' % grid
        # x_lo & x_hi are in local time, data is indexed in UTC
        start = self.x_lo - self.utcoffset
        stop = self.x_hi - self.utcoffset
        cumu_start = start
        if source == self.raw_data:
            boxwidth = 240      # assume 5 minute data interval
            start = source.before(start)
        elif source == self.hourly_data:
            boxwidth = 2800
            start = source.before(start)
            interval = timedelta(minutes=90)
        elif source == self.monthly_data:
            boxwidth = 2800 * 24 * 30
            interval = timedelta(days=46)
        else:
            interval = timedelta(hours=36)
            boxwidth = 2800 * 24
        boxwidth = eval(self.GetValue(plot, 'boxwidth', str(boxwidth)))
        result += 'set boxwidth %d\n' % boxwidth
        command = self.GetValue(plot, 'command', None)
        if command:
            result += '%s\n' % command
        stop = source.after(stop)
        if stop:
            stop = stop + timedelta(minutes=1)
        # write data files
        subplots = []
        for subplot_no in range(subplot_count):
            subplot = Record()
            subplot.subplot = subplot_list[subplot_no]
            subplot.dat_file = os.path.join(self.work_dir, 'plot_%d_%d.dat' % (
                plot_no, subplot_no))
            self.tmp_files.append(subplot.dat_file)
            subplot.dat = open(subplot.dat_file, 'w')
            subplot.xcalc = self.GetValue(subplot.subplot, 'xcalc', None)
            subplot.ycalc = self.GetValue(subplot.subplot, 'ycalc', None)
            subplot.cummulative = 'last_ycalc' in subplot.ycalc
            if subplot.xcalc:
                subplot.xcalc = compile(subplot.xcalc, '<string>', 'eval')
            subplot.ycalc = compile(subplot.ycalc, '<string>', 'eval')
            subplot.last_ycalcs = 0.0
            subplot.last_idx = None
            subplots.append(subplot)
        for data in source[start:stop]:
            for subplot in subplots:
                if subplot.xcalc:
                    idx = eval(subplot.xcalc)
                    if idx is None:
                        continue
                else:
                    idx = data['idx']
                idx += self.utcoffset
                if not subplot.cummulative and subplot.last_idx:
                    if source == self.raw_data:
                        interval = timedelta(minutes=((data['delay']*3)+1)//2)
                    if idx - subplot.last_idx > interval:
                        # missing data
                        subplot.dat.write('%s ?\n' % (idx.isoformat()))
                subplot.last_idx = idx
                try:
                    if subplot.cummulative and data['idx'] <= cumu_start:
                        value = 0.0
                    else:
                        last_ycalc = subplot.last_ycalcs
                        value = eval(subplot.ycalc)
                    subplot.dat.write('%s %g\n' % (idx.isoformat(), value))
                    subplot.last_ycalcs = value
                except TypeError:
                    if not subplot.cummulative:
                        subplot.dat.write('%s ?\n' % (idx.isoformat()))
                    subplot.last_ycalcs = 0.0
        for subplot in subplots:
            # ensure the data file isn't empty
            idx = self.x_hi + self.duration
            subplot.dat.write('%s ?\n' % (idx.isoformat()))
            subplot.dat.close()
        # plot data
        result += 'plot '
        colour = 0
        for subplot_no in range(subplot_count):
            subplot = subplots[subplot_no]
            colour = eval(self.GetValue(subplot.subplot, 'colour', str(colour+1)))
            style = self.GetValue(
                subplot.subplot, 'style', 'smooth unique lc %d lw 1' % (colour))
            words = style.split()
            if len(words) > 1 and words[0] in ('+', 'x', 'line'):
                width = int(words[1])
            else:
                width = 1
            if style == 'box':
                style = 'lc %d lw 0 with boxes' % (colour)
            elif words[0] == '+':
                style = 'lc %d lw %d pt 1 with points' % (colour, width)
            elif words[0] == 'x':
                style = 'lc %d lw %d pt 2 with points' % (colour, width)
            elif words[0] == 'line':
                style = 'smooth unique lc %d lw %d' % (colour, width)
            axes = self.GetValue(subplot.subplot, 'axes', 'x1y1')
            title = self.GetValue(subplot.subplot, 'title', '')
            result += ' "%s" using 1:($2) axes %s title "%s" %s' % (
                subplot.dat_file, axes, title, style)
            if subplot_no != subplot_count - 1:
                result += ', \\'
            result += '\n'
        if sys.version_info[0] < 3:
            result = result.encode(self.encoding)
        return result

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __usage__.strip()
            return 0
    # check arguments
    if len(args) != 4:
        print >>sys.stderr, 'Error: 4 arguments required\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    params = DataStore.params(args[0])
    status = DataStore.status(args[0])
    Localisation.SetApplicationLanguage(params)
    return GraphPlotter(
        params, status,
        DataStore.calib_store(args[0]), DataStore.hourly_store(args[0]),
        DataStore.daily_store(args[0]), DataStore.monthly_store(args[0]),
        args[1]
        ).DoPlot(args[2], args[3])

if __name__ == "__main__":
    sys.exit(main())
