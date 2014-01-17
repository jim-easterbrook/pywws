#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

Introduction
------------

Like Template.py this is one of the more difficult to use modules in
the weather station software collection. It plots a graph (or set of
graphs) of weather data. Almost everything about the graph is
controlled by an XML file. I refer to these files as templates, but
they aren't templates in the same sense as Template.py uses to create
text files.

Before writing your own graph template files, it might be useful to
look at some of the examples in the example_graph_templates directory.
If (like I was) you are unfamiliar with XML, I suggest reading the W3
Schools XML tutorial.

XML graph file syntax
^^^^^^^^^^^^^^^^^^^^^

Here is the simplest useful graph template. It plots the external
temperature for the last 24 hours. ::

  <?xml version="1.0" encoding="ISO-8859-1"?>
  <graph>
    <plot>
      <subplot>
        <title>Temperature (°C)</title>
        <ycalc>data['temp_out']</ycalc>
      </subplot>
    </plot>
  </graph>

In this example, the root element graph has one plot element, which
has one subplot element. The subplot element contains a title element
and a ycalc element. To plot more data on the same set of axes (for
example dew point and temperature), we can add more subplot elements.
To plot more than one set of axes (for example wind speed is measured
in different units from temperature) in the same file we can add more
plot elements.

The complete element hierarchy is shown below. ::

    graph
        plot
            subplot
                xcalc
                ycalc
                axes
                style
                colour
                title
            bmargin
            yrange
            y2range
            ytics
            y2tics
            ylabel
            ylabelangle
            y2label
            y2labelangle
            grid
            source
            boxwidth
            title
            command
        start
        stop
        duration
        layout
        size
        fileformat
        terminal
        lmargin
        rmargin
        xformat
        xlabel
        dateformat
        xtics
        title

graph
^^^^^

This is the root element of the graph XML file. It does not have to be
called "graph", but there must be exactly one root element.

plot
^^^^

Every graph element should contain at least one plot element. A
separate graph is drawn for each plot element, but all share the same
X axis.

start
^^^^^

This element sets the date & time of the start of the X axis. It is
used in the constructor of a Python datetime object. For example, to
start the graph at noon (local time) on Christmas day 2008:
``<start>year=2008, month=12, day=25, hour=12</start>``. The default
value is (stop - duration).

stop
^^^^

This element sets the date & time of the end of the X axis. It is used
in the constructor of a Python datetime object. For example, to end
the graph at 10 am (local time) on new year's day: ``<stop>year=2009,
month=1, day=1, hour=10</stop>``. The default value is (start +
duration), unless start is not defined in which case the timestamp of
the latest weather station hourly reading is used.

duration
^^^^^^^^

This element sets the extent of the X axis of the graph, unless both
start and stop are defined. It is used in the constructor of a Python
timedelta object. For example, to plot one week:
``<duration>weeks=1</duration>``. The default value is hours=24.

layout
^^^^^^

Controls the layout of the plots. Default is a single column. The
layout element specifies rows and columns. For example: ``<layout>4,
2</layout>`` will use a grid of 4 rows and 2 columns.

size
^^^^

Sets the overall dimensions of the image file containing the graph.
Default (in a single column layout) is a width of 600 pixels and
height of 200 pixels for each plot, so a graph with four plot elements
would be 600 x 800 pixels. Any size element must include both width
and height. For example: ``<size>800, 600</size>`` will produce an
image 800 pixels wide and 600 pixels high.

fileformat
^^^^^^^^^^

Sets the image format of the file containing the graph. Default is
png. Any string recognised by your installation of gnuplot should do.
For example: ``<fileformat>gif</fileformat>`` will produce a GIF
image.

terminal
^^^^^^^^

Allows complete control of gnuplot's 'terminal' settings. You may want
to use this if you are plotting to an unusual image format. Any string
recognised by your installation of gnuplot's 'set terminal' command
should do. For example: ``<terminal>svg enhanced font "arial,9" size
600,800 dynamic rounded</terminal>``. This setting overwrites both
size and fileformat.

lmargin
^^^^^^^

Sets the left margin of the plots, i.e. the distance from the left
hand axis to the left hand edge of the image area. According to the
gnuplot documentation the units of lmargin are character widths. The
default value is 5, which should look OK in most circumstances.

rmargin
^^^^^^^

Sets the right margin of the plots, i.e. the distance from the right
hand axis to the right hand edge of the image area. According to the
gnuplot documentation the units of rmargin are character widths. The
default value is -1, which sets automatic adjustment.

xformat
^^^^^^^

Sets the format of the time / date xtic labels. The value is a
strftime style format string. Default depends on the graph duration:
24 hours or less is "%%H%%M", 24 hours to 7 days is "%%a %%d" and 7
days or more is "%%Y/%%m/%%d".

xlabel
^^^^^^

Sets the X axis label. The value is a strftime style format string.
Default depends on the graph duration: 24 hours or less is "Time
(%%Z)", 24 hours to 7 days is "Day" and 7 days or more is "Date". The
datetime used to compute this is start, which may produce unexpected
results when a graph spans DST start or end.

dateformat
^^^^^^^^^^

Sets the format of the date labels at each end of X axis. The value is
a strftime style format string. Default is "%%Y/%%m/%%d". The right
hand label is only drawn if it differs from the left. To have no
labels, set an empty format: ``<dateformat></dateformat>``

xtics
^^^^^

Sets the spacing of the "tic" marks on the X axis. The value is an
integer number of hours. The default is to allow gnuplot to set an
appropriate interval.

title
^^^^^

Sets the title of the graph. A single line of text, for example:
``<title>Today's weather</title>``. This title appears at the very top
of the graph, outside any plot area.

subplot
^^^^^^^

Every plot element should contain at least one subplot element. A
separate trace is drawn for each subplot element, but all share the
same X and Y axes.

bmargin
^^^^^^^

Sets the bottom margin, i.e. the spacing between the lower X axis and
the edge of the graph (or the next plot). The default is to let
gnuplot adjust this automatically, which works OK most of the time but
you may wish to fine tune the value to suit your installation.

The permitted value is any non-negative real number. On my setup 0.9
is a good value, set as follows: ``<bmargin>0.9</bmargin>``.

yrange
^^^^^^

Sets the lower and upper limits of the (left hand) Y axis. The value
is anything understood by gnuplot, typically a pair of numbers. The
default is to allow gnuplot to set appropriate values, which is
unlikely to be what you want. For example, to plot typical UK
temperatures with no value going off the graph: ``<yrange>-10,
30</yrange>``. Note that commas are converted to colons, so
``<yrange>-10:30</yrange>`` would be equivalent.

You can use an asterisk to have gnuplot choose a suitable value. For
example, to have the upper value auto scale whilst fixing the lower
value at zero, use ``<yrange>0:*</yrange>``.

y2range
^^^^^^^

Sets the lower and upper limits of the right hand Y axis. Default is
for the right hand Y axis to be the same as the left, but setting a
different range is useful in dual axis plotting.

ytics
^^^^^

Controls the "tic" marks on the left hand Y axis. The value can be
anything that's understood by gnuplot. For example, to set the tic
spacing to 45 use ``<ytics>45</ytics>``. More complex things are also
possible, e.g. to label a wind direction graph with compass points,
use ``<y2tics>('N' 0, 'E' 90, 'S' 180, 'W' 270, 'N' 360)</y2tics>``.

y2tics
^^^^^^

Controls the "tic" marks on the right hand axis. The format is the
same as that for ytics. Default behaviour is to copy the left hand tic
marks, but without labels.

ylabel
^^^^^^

Adds a label to the (left hand) Y axis. For example, when plotting
temperature: ``<ylabel>°C</ylabel>``. If you use ylabel you will
probably want to adjust lmargin.

ylabelangle
^^^^^^^^^^^

Adjust the angle of the (left hand) Y axis label, if your version of
gnuplot supports it. For example, to write the label horizontally:
``<ylabelangle>90</ylabelangle>``.

y2label
^^^^^^^

Adds a label to the right hand Y axis. For example, when plotting
humidity: ``<y2label>%%</y2label>``. This is mostly used when plotting
dual axis graphs. If you use y2label you will probably want to adjust
rmargin.

y2labelangle
^^^^^^^^^^^^

Adjust the angle of the right hand Y axis label, if your version of
gnuplot supports it. For example, to write the label horizontally:
``<y2labelangle>90</y2labelangle>``.

grid
^^^^

Adds a grid to the plot. In most situations gnuplot's default grid is
suitable, so no value is needed: ``<grid></grid>``. More control is
possible using any of the options understood by gnuplot's set grid
command. For example, to have horizontal grid lines only:
``<grid>ytics</grid>``.

source
^^^^^^

Select the weather data to be plotted. Permitted values are
``<source>raw</source>``, ``<source>hourly</source>``,
``<source>daily</source>`` and ``<source>monthly</source>``. Default
is raw. Note that the different sources have different data
dictionaries, so this choice affects ycalc.

boxwidth
^^^^^^^^

Sets the width of the "boxes" used when drawing bar graphs. The value
is an integer expression yielding a number of seconds. Default depends
on source: raw is 240, hourly is 2800 and daily is 2800 * 24.

title
^^^^^

Sets the title of the plot. A single line of text, for example:
``<title>Temperature (°C)</title>``. This title appears within the
plot area, above any subplot titles.

command
^^^^^^^

Execute any gnuplot command, just before the main "plot" command. This
option allows advanced users to have greater control over the graph
appearance. The value is any valid gnuplot command, typically
beginning with the word set. For example: ``<command>set key tmargin
center horizontal width 1 noreverse enhanced autotitles box linetype
-1 linewidth 1</command>``. (Don't ask me what this example does — I'm
not an advanced user).

xcalc
^^^^^

Controls the X axis positioning of plotted data values. The default
value of data['idx'] is correct for most data, but there are some
exceptions. For example, when plotting bar charts of hourly rainfall,
it's nice to centre the bars on 30 minutes past the hour:
``<xcalc>data['idx'].replace(minute=30, second=0)</xcalc>``.

ycalc
^^^^^

Selects the data to be plotted. Any one line Python expression that
returns a single float value can be used. At its simplest this just
selects one value from the "data" dictionary, for example:
``<ycalc>data['temp_out']</ycalc>`` plots the external temperature.
More complex expressions are possible, and some helper functions are
provided. For example: ``<ycalc>dew_point(data['temp_out'],
data['hum_out'])</ycalc>`` plots the external dew point, and
``<ycalc>wind_mph(data['wind_ave'])</ycalc>`` plots the average wind
speed in miles per hour.

Cumulative plots are also possible. The result of each ycalc
computation is stored and made available to the next computation in
the variable last_ycalc. This can be used with any data, but is most
useful with rainfall: ``<ycalc>data['rain'] + last_ycalc</ycalc>``.

axes
^^^^

Selects which Y axis the data is plotted against. Default is the left
hand axis, but the right hand axis can be chosen with:
``<axes>x1y2</axes>``. This can be used in conjunction with y2range to
plot two unrelated quantities on one graph, for example temperature
and humidity.

style
^^^^^

Sets the line style for the graph. Default is a smooth continuous
line, thickness 1. To select a bar graph use: ``<style>box</style>``.
To select points without a connecting line use: ``<style>+</style>``
or ``<style>x</style>``. To select a line thickness 3 (for example)
use: ``<style>line 3</style>``. The thickness of points can be set in
a similar fashion. For complete control (for advanced users) a full
gnuplot style can be set: ``<style>smooth unique lc 5 lw 3</style>``.

colour
^^^^^^

Sets the colour of the subplot line or boxes. Any integer value is
accepted. The mapping of colours to numbers is set by gnuplot. Default
value is the previous colour plus one.

title
^^^^^

Sets the title of the subplot. A single line of text, for example:
``<title>Temperature (°C)</title>``. This title appears within the
plot area, next to a short segment of the line colour used for the
subplot.

Detailed API
------------

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
import locale
import logging
import os
import subprocess
import sys
import xml.dom.minidom

from pywws.conversions import *
from pywws import DataStore
from pywws import Localisation
from pywws.Logger import ApplicationLogger
from pywws.TimeZone import Local

class BasePlotter(object):
    def __init__(self, params, status, raw_data, hourly_data,
                 daily_data, monthly_data, work_dir):
        self.logger = logging.getLogger('pywws.%s' % self.__class__.__name__)
        self.raw_data = raw_data
        self.hourly_data = hourly_data
        self.daily_data = daily_data
        self.monthly_data = monthly_data
        self.work_dir = work_dir
        self.pressure_offset = eval(params.get('config', 'pressure offset'))
        self.gnuplot_version = eval(
            params.get('config', 'gnuplot version', '4.2'))
        # set language related stuff
        self.encoding = params.get('config', 'gnuplot encoding', 'iso_8859_1')
        # create work directory
        if not os.path.isdir(self.work_dir):
            os.makedirs(self.work_dir)

    def DoPlot(self, input_file, output_file):
        # read XML graph description
        self.doc = xml.dom.minidom.parse(input_file)
        self.graph = self.GetChildren(self.doc, 'graph')
        if not self.graph:
            self.logger.error('%s has no graph node' % input_file)
            self.doc.unlink()
            return 1
        self.graph = self.graph[0]
        # get list of plots
        plot_list = self.GetPlotList()
        self.plot_count = len(plot_list)
        if self.plot_count < 1:
            # nothing to plot
            self.logger.info('%s has no plot nodes' % input_file)
            self.doc.unlink()
            return 1
        # get start and end datetimes
        self.x_lo = self.GetValue(self.graph, 'start', None)
        self.x_hi = self.GetValue(self.graph, 'stop', None)
        self.duration = self.GetValue(self.graph, 'duration', None)
        if self.duration:
            self.duration = eval('timedelta(%s)' % self.duration)
        else:
            self.duration = timedelta(hours=24)
        if self.x_lo:
            self.x_lo = eval('datetime(%s)' % self.x_lo)
            if self.x_hi:
                self.x_hi = eval('datetime(%s)' % self.x_hi)
                self.duration = self.x_hi - self.x_lo
            else:
                self.x_hi = self.x_lo + self.duration
        elif self.x_hi:
            self.x_hi = eval('datetime(%s)' % self.x_hi)
            self.x_lo = self.x_hi - self.duration
        else:
            self.x_hi = self.hourly_data.before(datetime.max)
            if not self.x_hi:
                self.x_hi = datetime.utcnow()    # only if no hourly data
            self.x_hi += Local.utcoffset(self.x_hi)
            # set end of graph to start of the next hour after last item
            self.x_hi += timedelta(minutes=55)
            self.x_hi = self.x_hi.replace(minute=0, second=0)
            self.x_lo = self.x_hi - self.duration
        self.utcoffset = Local.utcoffset(self.x_hi)
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
        lcl = locale.getlocale()
        if lcl[0]:
            of.write('set locale "%s.%s"\n' % lcl)
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
                self.x_hi.replace(tzinfo=Local).strftime(xlabel))
            dateformat = '%Y/%m/%d'
            dateformat = self.GetValue(self.graph, 'dateformat', dateformat)
            if sys.version_info[0] < 3:
                dateformat = dateformat.encode(self.encoding)
            ldat = self.x_lo.replace(tzinfo=Local).strftime(dateformat)
            rdat = self.x_hi.replace(tzinfo=Local).strftime(dateformat)
            if ldat:
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
        if grid is not None:
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
    logger = ApplicationLogger(1)
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
