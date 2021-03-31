# -*- coding: utf-8 -*-
# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-21  pywws contributors

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

Like :py:mod:`pywws.template` this is one of the more difficult to use
modules in the weather station software collection. It plots a graph (or
set of graphs) of weather data. Almost everything about the graph is
controlled by an XML file. I refer to these files as templates, but they
aren't templates in the same sense as :py:mod:`pywws.template` uses to
create text files.

Before writing your own graph template files, it might be useful to
look at some of the examples in the example_graph_templates directory.
If (like I was) you are unfamiliar with XML, I suggest reading the W3
Schools XML tutorial.

Text encoding
^^^^^^^^^^^^^

The ``[config]`` section of :ref:`weather.ini <weather_ini-config>` has
a ``gnuplot encoding`` entry that sets the text encoding pywws uses to
write a gnuplot command file. The default value, ``iso_8859_1``, is
suitable for most western European languages, but may need changing if
you use another language. It can be set to any text encoding recognised
by both the Python :py:mod:`codecs` module and the `gnuplot
<http://www.gnuplot.info/documentation.html>`_ ``set encoding`` command.
If Python and gnuplot have different names for the same encoding, give
both names separated by a space, Python name first. For example::

    [config]
    gnuplot encoding = koi8_r koi8r

Note that you need to choose an encoding for which ``gnuplot`` has a
suitable font. You may need to set the font with a terminal_ element.
Note also that this encoding is unrelated to the encoding of your XML
graph file, which is set in the XML header.

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

In this example, the root element graph has one plot element, which has
one subplot element. The subplot element contains a title element and a
ycalc element. To plot more data on the same graph (for example dew
point and temperature), we can add more subplot elements. To plot more
than one graph (for example wind speed is measured in different units
from temperature) in the same file we can add more plot elements.

The complete element hierarchy is shown below.

|    graph_
|        plot_
|            subplot_
|                xcalc_
|                ycalc_
|                axes_
|                style_
|                colour_
|                :ref:`title <subplot-title>`
|            bmargin_
|            yrange_
|            y2range_
|            ytics_
|            y2tics_
|            ylabel_
|            ylabelangle_
|            y2label_
|            y2labelangle_
|            grid_
|            source_
|            boxwidth_
|            :ref:`title <plot-title>`
|            command_
|        start_
|        stop_
|        duration_
|        layout_
|        size_
|        fileformat_
|        terminal_
|        lmargin_
|        rmargin_
|        xformat_
|        xlabel_
|        dateformat_
|        xtics_
|        :ref:`title <graph-title>`

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
used in the ``replace`` method of a Python datetime object that is
initialised to 00:00 hours on the date of the latest weather station
hourly reading. For example, to start the graph at noon (local time)
on Christmas day 2008: ``<start>year=2008, month=12, day=25,
hour=12</start>`` or to start the graph at 2am (local time) today:
``<start>hour=2</start>``. The default value is (stop - duration).

.. versionadded:: 14.06.dev1238
   previously the ``<start>`` and ``<stop>`` elements were used in a
   datetime constructor, so ``year``, ``month`` and ``day`` values
   were required.

stop
^^^^

This element sets the date & time of the end of the X axis. It is used
in the ``replace`` method of a Python datetime object, just like
``<start>``. The default value is (start + duration), unless start is
not defined, in which case the timestamp of the latest weather station
hourly reading is used.

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
``png``. Any string recognised by your installation of gnuplot should
do. For example: ``<fileformat>gif</fileformat>`` will produce a GIF
image.

If your installation of gnuplot supports it, ``pngcairo`` is an
alternative to ``png`` that can yield much better looking results.

.. versionadded:: 15.11.0.dev1331
   You can also set terminal_ options in this string, for example:
   ``<fileformat>pngcairo font "arial,8" rounded</fileformat>`` will use
   a small "Arial" font and round the ends of line segments.

terminal
^^^^^^^^

Allows complete control of gnuplot's "terminal" settings. You may want
to use this if you are plotting to an unusual image format. Any string
recognised by your installation of gnuplot's 'set terminal' command
should do. For example: ``<terminal>svg enhanced font "arial,9" dynamic
rounded size 600,800</terminal>``. This setting overwrites both size_
and fileformat_.

.. versionchanged:: 15.11.0.dev1331
   The size_ and fileformat_ elements are now the preferred way to set
   the gnuplot "terminal".

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

.. _graph-title:

title
^^^^^

Sets the title of the graph. A single line of text, for example:
``<title>Today's weather</title>``. This title appears at the very top
of the graph, outside any plot area.

.. versionadded:: 15.06.0.dev1301
   If the title contains any "%%" characters it will be used as a
   strftime style format string for the datetime of the stop value. This
   allows you to include the graph's date or time in the title.

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

Since gnuplot version 4.6 you can set lower and/or upper bounds of the
auto scaled range. The gnuplot syntax for this is ``lo < * < hi``, but
as the plot template is an XML file we need to replace the ``<``
characters with ``&lt;``. For example, if we want the upper value to
always be 20 or more we can use ``<yrange>0:20 &lt; *</yrange>``.

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

.. _plot-title:

title
^^^^^

Sets the title of the plot. A single line of text, for example:
``<title>Temperature (°C)</title>``. This title appears within the
plot area, above any :ref:`subplot titles <subplot-title>`.

command
^^^^^^^

Execute any gnuplot command, just before the main "plot" command. This
option allows advanced users to have greater control over the graph
appearance. The value is any valid gnuplot command, typically
beginning with the word set. For example: ``<command>set key tmargin
center horizontal width 1 noreverse enhanced autotitles box linetype
-1 linewidth 1</command>``. (Don't ask me what this example does — I'm
not an advanced user).

.. versionadded:: 15.11.0.dev1333
   This element can be repeated to allow several things to be set.

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

In addition to the functions in the :py:mod:`pywws.conversions` module
there are four more useful functions: ``rain_hour(data)`` returns the
amount of rain in the last hour, ``rain_day(data)`` returns the amount
of rain since midnight (local time), ``rain_24hr(data)`` returns the
amount of rain in the last 24 hours, and ``hour_diff(data, key)``
returns the change in data item ``key`` over the last hour.

Cumulative plots are also possible. The result of each ycalc
computation is stored and made available to the next computation in
the variable last_ycalc. This can be used with any data, but is most
useful with rainfall: ``<ycalc>data['rain'] + last_ycalc</ycalc>``.

A special case are plots with ``<style>candlesticks</style>`` or
``<style>candlesticksw</style>`` which need 4 values in a specific
order: ``<ycalc>(data['temp_out_min_ave'], data['temp_out_min_lo'],
data['temp_out_max_hi'], data['temp_out_max_ave'])</ycalc>``. To add
a median bar, use another candlesticks plot with
``data['temp_out_ave']`` in all 4 fields.

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

For candlesticks plots you can specify line thickness as well, e.g.
``<style>candlesticks 1.5</style>``. If you add whiskerbars, you can
change the width of the whiskerbars with a second parameter, e.g.
``<style>candlesticksw 2 0.5</style>`` would plot the whiskerbars with
50%% width of the candlesticks.

colour
^^^^^^

Sets the colour of the subplot line or boxes. This can be in any form
that gnuplot accepts, typically a single integer or an rgb specification
such as ``rgb "cyan"`` or ``rgb "FF00FF"``. The mapping of integer
values to colours is set by gnuplot. Default value is an ever
incrementing integer.

.. _subplot-title:

title
^^^^^

Sets the title of the subplot. A single line of text, for example:
``<title>Temperature (°C)</title>``. This title appears within the
plot area, next to a short segment of the line colour used for the
subplot.

Detailed API
------------

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.plot [options] data_dir temp_dir xml_file output_file
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

from pywws.constants import DAY, HOUR
from pywws.conversions import *
import pywws.localisation
import pywws.logger
import pywws.storage
from pywws.template import Computations
from pywws.timezone import time_zone

logger = logging.getLogger(__name__)


class GraphNode(object):
    def __init__(self, node):
        self.node = node

    def get_children(self, name):
        result = []
        for child in self.node.childNodes:
            if child.localName == name:
                result.append(GraphNode(child))
        return result

    def get_value(self, name, default):
        for child in self.node.childNodes:
            if child.localName == name:
                if child.childNodes:
                    return child.childNodes[0].data.strip()
                else:
                    return ''
        return default

    def get_values(self, name):
        for child in self.node.childNodes:
            if child.localName == name:
                if child.childNodes:
                    yield child.childNodes[0].data.strip()


class GraphFileReader(GraphNode):
    def __init__(self, input_file):
        self.input_file = input_file
        self.doc = GraphNode(xml.dom.minidom.parse(input_file))
        graphs = self.doc.get_children('graph')
        if not graphs:
            raise RuntimeError('%s has no graph node' % input_file)
        super(GraphFileReader, self).__init__(graphs[0].node)

    def close(self):
        self.doc.node.unlink()


class BasePlotter(object):
    def __init__(self, context, work_dir):
        self.calib_data = context.calib_data
        self.hourly_data = context.hourly_data
        self.daily_data = context.daily_data
        self.monthly_data = context.monthly_data
        self.work_dir = work_dir
        self.pressure_offset = float(
            context.params.get('config', 'pressure offset'))
        self.gnuplot_version = float(
            context.params.get('config', 'gnuplot version', '4.2'))
        self.computations = Computations(context)
        # set language related stuff
        self.encoding = context.params.get(
            'config', 'gnuplot encoding', 'iso_8859_1')
        if ' ' in self.encoding:
            self.encoding = self.encoding.split()
        else:
            self.encoding = [self.encoding, self.encoding]
        # check work directory exists
        if not os.path.isdir(self.work_dir):
            raise RuntimeError(
                'Directory "' + self.work_dir + '" does not exist.')

    def _eval_time(self, time_str):
        # get timestamp of last data item
        result = self.hourly_data.before(datetime.max)
        if not result:
            result = datetime.utcnow()    # only if no hourly data
        # convert to local time
        result = time_zone.utc_to_local(result)
        # set to start of the day
        result = result.replace(hour=0, minute=0, second=0, microsecond=0)
        # apply time string
        result = eval('result.replace(%s)' % time_str)
        # convert back to UTC
        return time_zone.local_to_utc(result)

    def do_plot(self, input_file, output_file):
        if isinstance(input_file, GraphFileReader):
            self.graph = input_file
        else:
            # read XML graph description
            self.graph = GraphFileReader(input_file)
        # get list of plots
        plot_list = self.graph.get_children(self.plot_name)
        self.plot_count = len(plot_list)
        if self.plot_count < 1:
            # nothing to plot
            logger.info('%s has no %s nodes', self.graph.input_file, self.plot_name)
            self.graph.close()
            return 1
        # get start and end datetimes
        self.x_lo = self.graph.get_value('start', None)
        self.x_hi = self.graph.get_value('stop', None)
        self.duration = self.graph.get_value('duration', None)
        if self.duration:
            self.duration = eval('timedelta(%s)' % self.duration)
        else:
            self.duration = DAY
        if self.x_lo:
            self.x_lo = self._eval_time(self.x_lo)
            if self.x_hi:
                self.x_hi = self._eval_time(self.x_hi)
                self.duration = self.x_hi - self.x_lo
            else:
                self.x_hi = self.x_lo + self.duration
        elif self.x_hi:
            self.x_hi = self._eval_time(self.x_hi)
            self.x_lo = self.x_hi - self.duration
        else:
            self.x_hi = self.hourly_data.before(datetime.max)
            if not self.x_hi:
                self.x_hi = datetime.utcnow()    # only if no hourly data
            if self.duration < HOUR * 6:
                # set end of graph to start of the next minute after last item
                self.x_hi += timedelta(seconds=55)
                self.x_hi = self.x_hi.replace(second=0)
            else:
                # set end of graph to start of the next hour after last item
                self.x_hi += timedelta(minutes=55)
                self.x_hi = self.x_hi.replace(minute=0, second=0)
            self.x_lo = self.x_hi - self.duration
        # use a fixed offset to convert UTC to X axis values
        self.utcoffset = time_zone.utc_to_local(self.x_hi).replace(
            tzinfo=None) - self.x_hi
        # open gnuplot command file
        self.tmp_files = []
        cmd_file = os.path.join(self.work_dir, 'plot.cmd')
        self.tmp_files.append(cmd_file)
        of = codecs.open(cmd_file, 'w', encoding=self.encoding[0])
        # write gnuplot set up
        of.write('set encoding %s\n' % (self.encoding[1]))
        lcl = locale.getlocale()
        if lcl[0]:
            of.write('set locale "%s.%s"\n' % lcl)
        self.rows = self.get_default_rows()
        self.cols = (self.plot_count + self.rows - 1) // self.rows
        self.rows, self.cols = eval(self.graph.get_value(
            'layout', '%d, %d' % (self.rows, self.cols)))
        w, h = self.get_default_plot_size()
        w = w * self.cols
        h = h * self.rows
        w, h = eval(self.graph.get_value('size', '(%d, %d)' % (w, h)))
        fileformat = self.graph.get_value('fileformat', 'png')
        if fileformat == 'svg':
            terminal = 'svg enhanced font "arial,9" dynamic rounded'
        elif u' ' not in fileformat:
            terminal = '%s large' % (fileformat)
        else:
            terminal = fileformat
        if u'size' not in terminal:
            terminal += u' size %d,%d' % (w, h)
        terminal = self.graph.get_value('terminal', terminal)
        of.write('set terminal %s\n' % (terminal))
        of.write('set output "%s"\n' % (output_file))
        # set overall title
        title = self.graph.get_value('title', '')
        if title:
            if '%' in title:
                x_hi = time_zone.utc_to_local(self.x_hi)
                if sys.version_info[0] < 3:
                    title = title.encode(self.encoding[0])
                title = x_hi.strftime(title)
                if sys.version_info[0] < 3:
                    title = title.decode(self.encoding[0])
            title = 'title "%s"' % title
        of.write('set multiplot layout %d, %d %s\n' % (self.rows, self.cols, title))
        # do actual plots
        of.write(self.get_preamble())
        for plot_no in range(self.plot_count):
            plot = plot_list[plot_no]
            # set key / title location
            title = plot.get_value('title', '')
            of.write('set key horizontal title "%s"\n' % title)
            # optional yaxis labels
            ylabel = plot.get_value('ylabel', '')
            if ylabel:
                ylabelangle = plot.get_value('ylabelangle', '')
                if ylabelangle:
                    ylabelangle = ' rotate by %s' % (ylabelangle)
                of.write('set ylabel "%s"%s\n' % (ylabel, ylabelangle))
            else:
                of.write('set ylabel\n')
            y2label = plot.get_value('y2label', '')
            if y2label:
                y2labelangle = plot.get_value('y2labelangle', '')
                if y2labelangle:
                    y2labelangle = ' rotate by %s' % (y2labelangle)
                of.write('set y2label "%s"%s\n' % (y2label, y2labelangle))
            else:
                of.write('set y2label\n')
            # set data source
            source = plot.get_value('source', 'raw')
            if source == 'raw':
                source = self.calib_data
            elif source == 'hourly':
                source = self.hourly_data
            elif source == 'monthly':
                source = self.monthly_data
            else:
                source = self.daily_data
            # do the plot
            of.write(self.plot_data(plot_no, plot, source))
        of.close()
        self.graph.close()
        # run gnuplot on file
        subprocess.check_call(['gnuplot', cmd_file])
        for file in self.tmp_files:
            os.unlink(file)
        return 0


class GraphPlotter(BasePlotter):
    plot_name = 'plot'
    def get_default_rows(self):
        return self.plot_count

    def get_default_plot_size(self):
        return 200 // self.cols, 600 // self.cols

    def get_preamble(self):
        result = u"""set style fill solid
set xdata time
set timefmt "%Y-%m-%dT%H:%M:%S"
"""
        result += u'set xrange ["%s":"%s"]\n' % (
            (self.x_lo + self.utcoffset).isoformat(),
            (self.x_hi + self.utcoffset).isoformat())
        lmargin = eval(self.graph.get_value('lmargin', '5'))
        result += u'set lmargin %g\n' % (lmargin)
        rmargin = eval(self.graph.get_value('rmargin', '-1'))
        result += u'set rmargin %g\n' % (rmargin)
        if self.duration <= DAY:
            xformat = '%H%M'
        elif self.duration <= timedelta(days=7):
            xformat = '%a %d'
        else:
            xformat = '%Y/%m/%d'
        xformat = self.graph.get_value('xformat', xformat)
        result += u'set format x "%s"\n' % xformat
        xtics = self.graph.get_value('xtics', None)
        if xtics:
            result += u'set xtics %d\n' % (eval(xtics) * 3600)
        return result

    def plot_data(self, plot_no, plot, source):
        class Record(object):
            pass

        _ = pywws.localisation.translation.ugettext
        subplot_list = plot.get_children('subplot')
        subplot_count = len(subplot_list)
        if subplot_count < 1:
            return u''
        result = u''
        pressure_offset = self.pressure_offset
        # add some useful functions
        hour_diff = self.computations.hour_diff
        rain_hour = self.computations.rain_hour
        rain_day = self.computations.rain_day
        rain_24hr = self.computations.rain_24hr
        # label x axis of last plot
        if plot_no == self.plot_count - 1:
            x_lo = time_zone.utc_to_local(self.x_lo)
            x_hi = time_zone.utc_to_local(self.x_hi)
            if self.duration <= DAY:
                # TX_NOTE Keep the "(%Z)" formatting string
                xlabel = _('Time (%Z)')
            elif self.duration <= timedelta(days=7):
                xlabel = _('Day')
            else:
                xlabel = _('Date')
            xlabel = self.graph.get_value('xlabel', xlabel)
            if sys.version_info[0] < 3:
                xlabel = xlabel.encode(self.encoding[0])
            xlabel = x_hi.strftime(xlabel)
            if sys.version_info[0] < 3:
                xlabel = xlabel.decode(self.encoding[0])
            result += u'set xlabel "%s"\n' % xlabel
            dateformat = '%Y/%m/%d'
            dateformat = self.graph.get_value('dateformat', dateformat)
            if sys.version_info[0] < 3:
                dateformat = dateformat.encode(self.encoding[0])
            ldat = x_lo.strftime(dateformat)
            rdat = x_hi.strftime(dateformat)
            if sys.version_info[0] < 3:
                ldat = ldat.decode(self.encoding[0])
                rdat = rdat.decode(self.encoding[0])
            if ldat:
                result += u'set label "%s" at "%s", graph -0.3 left\n' % (
                    ldat, (self.x_lo + self.utcoffset).isoformat())
            if rdat != ldat:
                result += u'set label "%s" at "%s", graph -0.3 right\n' % (
                    rdat, (self.x_hi + self.utcoffset).isoformat())
        # set bottom margin
        bmargin = eval(plot.get_value('bmargin', '-1'))
        result += u'set bmargin %g\n' % (bmargin)
        # set y ranges and tics
        yrange = plot.get_value('yrange', None)
        y2range = plot.get_value('y2range', None)
        ytics = plot.get_value('ytics', 'autofreq')
        y2tics = plot.get_value('y2tics', '')
        if y2tics and not y2range:
            y2range = yrange
        elif y2range and not y2tics:
            y2tics = 'autofreq'
        if yrange:
            result += u'set yrange [%s]\n' % (yrange.replace(',', ':'))
        else:
            result += u'set yrange [*:*]\n'
        if y2range:
            result += u'set y2range [%s]\n' % (y2range.replace(',', ':'))
        if y2tics:
            result += u'set ytics nomirror %s; set y2tics %s\n' % (ytics, y2tics)
        else:
            result += u'unset y2tics; set ytics mirror %s\n' % (ytics)
        # set grid
        result += u'unset grid\n'
        grid = plot.get_value('grid', None)
        if grid is not None:
            result += u'set grid %s\n' % grid
        start = self.x_lo
        stop = self.x_hi
        cumu_start = start
        if source == self.calib_data:
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
        boxwidth = eval(plot.get_value('boxwidth', str(boxwidth)))
        result += u'set boxwidth %d\n' % boxwidth
        for command in plot.get_values('command'):
            result += u'%s\n' % command
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
            subplot.xcalc = subplot.subplot.get_value('xcalc', None)
            subplot.ycalc = subplot.subplot.get_value('ycalc', None)
            subplot.cummulative = 'last_ycalc' in subplot.ycalc
            if subplot.xcalc:
                subplot.xcalc = compile(subplot.xcalc, '<string>', 'eval')
            subplot.ycalc = compile(subplot.ycalc, '<string>', 'eval')
            subplot.last_ycalcs = 0.0
            subplot.last_idx = None
            subplot.using = '($2)'
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
                    if source == self.calib_data:
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
                    if not isinstance(value, tuple):
                        value = (value,)
                    values = (idx.isoformat(),) + value
                    vformat = '%s' + (' %g' * len(value)) + '\n'
                    subplot.dat.write(vformat % values)
                    subplot.using = ':'.join(
                        '($%d)' % x for x in range(2, len(values)+1))
                    subplot.last_ycalcs = value[0]
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
        result += u'plot '
        colour_idx = 0
        for subplot_no in range(subplot_count):
            subplot = subplots[subplot_no]
            colour_idx += 1
            colour = subplot.subplot.get_value('colour', str(colour_idx))
            style = subplot.subplot.get_value(
                'style', 'smooth unique lc %s lw 1' % (colour))
            words = style.split()
            if len(words) > 1 and words[0] in ('+', 'x', 'line', 'candlesticks', 'candlesticksw'):
                width = float(words[1])
            else:
                width = 1
            if len(words) > 2 and words[0] in ('candlesticksw'):
                whiskerwidth = float(words[2])
            else:
                whiskerwidth = 1
            whiskerbars = ''
            if style == 'box':
                style = 'lc %s lw 0 with boxes' % (colour)
            elif words[0] == 'candlesticks':
                style = 'lc %s lw %g with candlesticks' % (colour, width)
            elif words[0] == 'candlesticksw':
                style = 'lc %s lw %g with candlesticks' % (colour, width)
                whiskerbars = ' whiskerbars %g' % (whiskerwidth)
            elif words[0] == '+':
                style = 'lc %s lw %g pt 1 with points' % (colour, width)
            elif words[0] == 'x':
                style = 'lc %s lw %g pt 2 with points' % (colour, width)
            elif words[0] == 'line':
                style = 'smooth unique lc %s lw %g' % (colour, width)
            axes = subplot.subplot.get_value('axes', 'x1y1')
            title = subplot.subplot.get_value('title', '')
            result += u' "%s" using 1:%s axes %s %s title "%s"%s' % (
                subplot.dat_file, subplot.using, axes, style, title, whiskerbars)
            if subplot_no != subplot_count - 1:
                result += u', \\'
            result += u'\n'
        return result


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 1
    # process options
    for o, a in opts:
        if o == '-h' or o == '--help':
            print(__usage__.strip())
            return 0
    # check arguments
    if len(args) != 4:
        print('Error: 4 arguments required\n', file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 2
    pywws.logger.setup_handler(2)
    with pywws.storage.pywws_context(args[0]) as context:
        pywws.localisation.set_application_language(context.params)
        return GraphPlotter(context, args[1]).do_plot(
            GraphFileReader(args[2]), args[3])


if __name__ == "__main__":
    sys.exit(main())
