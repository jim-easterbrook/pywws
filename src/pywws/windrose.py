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

"""Plot a "wind rose"

::

%s

Introduction
------------

This routine plots one or more "wind roses" (see `Wikipedia
<http://en.wikipedia.org/wiki/Wind_rose>`_ for a description). Like
:py:mod:`pywws.plot` almost everything is controlled by an XML
"recipe" / template file.

Before writing your own template files, it might be useful to look at
some of the examples in the example_graph_templates directory. If
(like I was) you are unfamiliar with XML, I suggest reading the `W3
Schools XML tutorial <http://www.w3schools.com/xml/>`_.

XML graph file syntax
---------------------

Here is the simplest useful wind rose template. It plots wind over the
last 24 hours. ::

  <?xml version="1.0" encoding="ISO-8859-1"?>
  <graph>
    <windrose>
      <ycalc>data['wind_ave']</ycalc>
    </windrose>
  </graph>

In this example, the root element graph has one windrose element which
contains nothing more than a ycalc element.

The complete element hierarchy is shown below.

|    graph_
|        windrose_
|            xcalc_
|            ycalc_
|            threshold_
|            colour_
|            yrange_
|            points_
|            source_
|            :ref:`title <rose-title>`
|            command_
|        start_
|        stop_
|        duration_
|        layout_
|        size_
|        fileformat_
|        `lmargin, rmargin, tmargin, bmargin`_
|        :ref:`title <roses-title>`

graph
^^^^^

This is the root element of the graph XML file. It does not have to be
called "graph", but there must be exactly one root element.

start
^^^^^

This element sets the date & time of the wind roses. It is used in the
constructor of a Python datetime object. For example, to start at noon
(local time) on Christmas day 2008: ``<start>year=2008, month=12,
day=25, hour=12</start>``. The default value is (stop - duration).

stop
^^^^

This element sets the date & time of the end of the wind roses. It is
used in the constructor of a Python datetime object. For example, to
end at 10 am (local time) on new year's day 2009: ``<stop>year=2009,
month=1, day=1, hour=10</stop>``. The default value is (start +
duration), unless start is not defined in which case the timestamp of
the latest weather station hourly reading is used.

duration
^^^^^^^^

This element sets the duration of wind roses, unless both start and
stop are defined. It is used in the constructor of a Python timedelta
object. For example, to plot one week:
``<duration>weeks=1</duration>``. The default value is hours=24.

layout
^^^^^^

Controls the layout of the plots. Default is a grid that is wider than
it is tall. The layout element specifies rows and columns. For
example: ``<layout>4, 2</layout>`` will use a grid of 4 rows and 2
columns.

size
^^^^

Sets the overall dimensions of the image file containing the graph.
Default is a height of 600 pixels and a width that depends on the
layout. Any size element must include both width and height. For
example: ``<size>800, 600</size>`` will produce an image 800 pixels
wide and 600 pixels high.

fileformat
^^^^^^^^^^

Sets the image format of the file containing the plots. Default is
png. Any string recognised by your installation of gnuplot should do.
For example: ``<fileformat>gif</fileformat>`` will produce a GIF
image.

lmargin, rmargin, tmargin, bmargin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Over-rides the automatically computed left, right, top or bottom
margin. Supply any positive real number, for example
``<lmargin>1.3</lmargin>``. Some experimentation may be necessary to
find the best values.

.. _roses-title:

title
^^^^^

Sets the overall title of the plots. A single line of text, for example:
``<title>Today's wind direction</title>``. This title appears at the
very top, outside any plot area.

.. versionadded:: 15.06.0.dev1301
   If the title contains any "%%" characters it will be used as a
   strftime style format string for the datetime of the stop value. This
   allows you to include the graph's date or time in the title, for
   example: ``<title>Wind over 24 hours ending %%H:%%M (mph)</title>``

windrose
^^^^^^^^

A separate plot is drawn for each windrose element, but all share the
same time period.

xcalc
^^^^^

Selects if data is included in the wind rose. The value should be a
valid Python logical expression. For example, to plot a rose for
afternoon winds only: ``<xcalc>data['idx'].hour &gt;= 12</xcalc>``.
This allows aggregation of afternoon wind data over several days.
Remember that data is indexed in UTC, so you need to use an expression
that takes account of your time zone. The default value is 'True'.

ycalc
^^^^^

Selects the data to be plotted. Any one line Python expression that
returns a single float value can be used. At its simplest this just
selects one value from the "data" dictionary, for example:
``<ycalc>data['wind_ave']</ycalc>``. To convert to mph use:
``<ycalc>data['wind_ave'] * 3.6 / 1.609344</ycalc>``. You are unlikely
to want to use anything other than 'wind_ave' here.

threshold
^^^^^^^^^

Sets the thresholds for each colour on the rose petals. Defaults are
based on the Wikipedia example. The values should be a correctly
ordered list of real numbers, for example: ``<threshold>0.5, 3.5, 7.5,
12.5, 18.5, 24.5, 31.5</threshold>`` approximates to the Beaufort
scale, if ycalc has been set to convert windspeeds to mph.

colour
^^^^^^

Sets the colours of the threshold petal segments. Can be any sequence of
values accepted by gnuplot. Default value is a sequence of integer
colour indexes, which is probably not what you want. You may need to
experiment with more complicated values such as ::

  <colour>'rgb "grey"','rgb "#0000FF"','rgb "#00A080"','rgb "#00FF00"','rgb "#A0FF00"','rgb "#FFFF00"'</colour>

yrange
^^^^^^

Sets the upper limits of the axes. The rose shows what percentage of
the time the wind came from a particular direction. For example, if
you live somewhere with a very steady wind you might want to allow
higher percentages than normal: ``<yrange>91</yrange>``. Auto-scaling
is also possible, using an asterisk: ``<yrange>*</yrange>``

points
^^^^^^

Sets the text of the compass points. The defaults are 'N', 'S', 'E' &
'W'. For graphs in another language you can over-ride this, for example:
``<points>'No', 'Zu', 'Oo', 'We'</points>``. (The preferred way to do
this is to create a language file, see :py:mod:`pywws.localisation`.)

source
^^^^^^

Select the weather data to be plotted. Permitted values are
``<source>raw</source>``, ``<source>hourly</source>``,
``<source>daily</source>`` and ``<source>monthly</source>``. Default
is raw. Note that the different sources have different data
dictionaries, so this choice affects ycalc.

.. _rose-title:

title
^^^^^

Sets the title of the plot. A single line of text, for example:
``<title>Morning winds</title>``. This title appears within the plot
area, above the threshold colour key.

command
^^^^^^^

.. versionadded:: 16.06.0

Execute any gnuplot command, just before the main "plot" command. This
option allows advanced users to have greater control over the graph
appearance. The value is any valid gnuplot command, typically
beginning with the word set.

For example, ``<command>set grid front</command>`` will stop the grid
being hidden by the coloured wedges, and ``<command>set key outside
above right maxrows 1</command>`` will place the key outside the plot
area.

Detailed API
------------

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.windrose [options] data_dir temp_dir xml_file output_file
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
import math
import os
import sys
import xml.dom.minidom

from pywws.conversions import *
import pywws.localisation
import pywws.logger
from pywws.plot import BasePlotter
import pywws.storage


class RosePlotter(BasePlotter):
    plot_name = 'windrose'
    def get_default_rows(self):
        return int(math.sqrt(self.plot_count))

    def get_default_plot_size(self):
        return 600 // self.rows, 600 // self.rows

    def get_preamble(self):
        result = u"""set polar
set angles degrees
set zeroaxis
set grid polar 22.5
set size square
unset border
set xtics axis
unset ytics
"""
        if self.gnuplot_version >= 4.4:
            result += u'set style fill solid noborder\n'
        if self.gnuplot_version >= 4.6:
            result += u"""unset raxis
set rtics format ''
"""
        lmargin = eval(self.graph.get_value('lmargin', '-1'))
        result += u'set lmargin %g\n' % (lmargin)
        lmargin = eval(self.graph.get_value('rmargin', '-1'))
        result += u'set rmargin %g\n' % (lmargin)
        lmargin = eval(self.graph.get_value('tmargin', '-1'))
        result += u'set tmargin %g\n' % (lmargin)
        lmargin = eval(self.graph.get_value('bmargin', '-1'))
        result += u'set bmargin %g\n' % (lmargin)
        return result

    def plot_data(self, plot_no, plot, source):
        _ = pywws.localisation.translation.ugettext
        # get statistics
        thresh = eval(plot.get_value(
            'threshold', '0.0, 1.54, 3.09, 5.14, 8.23, 10.8, 15.5'))
        thresh = thresh + (1000.0,)
        colour = eval(plot.get_value('colour', str(range(len(thresh)))))
        xcalc = plot.get_value('xcalc', 'True')
        xcalc = compile(xcalc, '<string>', 'eval')
        ycalc = plot.get_value('ycalc', None)
        ycalc = compile(ycalc, '<string>', 'eval')
        histograms = []
        for i in range(len(thresh)):
            hist = []
            for n in range(16):
                hist.append(0)
            histograms.append(hist)
        start = self.x_lo
        stop = self.x_hi
        stop = stop + timedelta(minutes=1)
        for data in source[start:stop]:
            wind_dir = data['wind_dir']
            if wind_dir is None:
                continue
            if not isinstance(wind_dir, int):
                wind_dir = int(wind_dir + 0.5) % 16
            if not eval(xcalc):
                continue
            value = eval(ycalc)
            if value is None:
                continue
            for t in range(len(thresh)):
                if value <= thresh[t]:
                    histograms[t][wind_dir] += 1
                    break
        # evenly distribute zero speed
        total = 0
        for n in range(16):
            total += histograms[0][n]
        for n in range(16):
            histograms[0][n] = float(total) / 16.0
        # integrate histograms
        for i in range(1, len(thresh)):
            for n in range(16):
                histograms[i][n] += histograms[i-1][n]
        total = 0.0
        for n in range(16):
            total += histograms[-1][n]
        result = u''
        yrange = plot.get_value('yrange', '31')
        if yrange == '*':
            # auto-ranging
            if total > 0:
                max_petal = 100.0 * float(max(histograms[-1])) / total
            else:
                max_petal = 0.0
            if max_petal > 40.0:
                yrange = (int(max_petal / 20.0) * 20) + 21
            elif max_petal > 30.0:
                yrange = 41
            elif max_petal > 20.0:
                yrange = 31
            else:
                yrange = 21
        else:
            yrange = eval(yrange)
        result += u'set rrange [0:%f]\n' % (yrange)
        result += u'set xrange [-%f:%f]\n' % (yrange, yrange)
        result += u'set yrange [-%f:%f]\n' % (yrange, yrange)
        points = [_('N'), _('S'), _('E'), _('W')]
        points = eval(plot.get_value('points', str(points)))
        result += u'set label 1000 "%s" at 0, %d center front\n' % (points[0], yrange + 1)
        result += u'set label 1001 "%s" at 0, -%d center front\n' % (points[1], yrange + 1)
        result += u'set label 1002 "%s" at %d, 0 center front\n' % (points[2], yrange + 1)
        result += u'set label 1003 "%s" at -%d, 0 center front\n' % (points[3], yrange + 1)
        # additional commands for gnuplot
        for command in plot.get_values('command'):
            result += u'%s\n' % command
        # plot segments for each speed-direction
        result += u'plot '
        for i in reversed(range(len(thresh))):
            dat_file = os.path.join(self.work_dir, 'plot_%d_%d.dat' % (plot_no, i))
            self.tmp_files.append(dat_file)
            dat = open(dat_file, 'w')
            sub_total = 0
            if i == 0:
                for n in range(16):
                    sub_total += histograms[i][n]
                if total > 0:
                    value = 100.0 * float(histograms[i][0]) / float(total)
                else:
                    value = 0.0
                if self.gnuplot_version >= 4.4:
                    dat.write('0 0 %g 0 360\n' % (value))
                else:
                    for n in range(16):
                        angle = 90.0 - (n * 22.5)
                        dat.write('%g %g\n' % (angle - 11.24, value * 0.994))
                        dat.write('%g %g\n' % (angle - 8.0, value * 0.997))
                        dat.write('%g %g\n' % (angle, value))
                        dat.write('%g %g\n' % (angle + 8.0, value * 0.997))
                        dat.write('%g %g\n' % (angle + 11.24, value * 0.994))
                        dat.write('%g %g\n' % (angle + 11.25, 0))
            else:
                for n in range(16):
                    angle = 90.0 - (n * 22.5)
                    sub_total += histograms[i][n]
                    sub_total -= histograms[i-1][n]
                    if total > 0:
                        value = 100.0 * float(histograms[i][n]) / float(total)
                    else:
                        value = 0.0
                    if self.gnuplot_version >= 4.4:
                        dat.write(
                            '0 0 %g %g %g\n' % (value, angle - 10, angle + 10))
                    else:
                        dat.write('%g %g\n' % (angle - 8.1, 0))
                        dat.write('%g %g\n' % (angle - 8.0, value * 0.997))
                        dat.write('%g %g\n' % (angle, value))
                        dat.write('%g %g\n' % (angle + 8.0, value * 0.997))
                        dat.write('%g %g\n' % (angle + 8.1, 0))
            dat.close()
            # plot data
            if total > 0:
                value = 100.0 * float(sub_total) / float(total)
            else:
                value = 0.0
            if i == 0:
                title = '0 .. %g (%.3g%%)' % (thresh[i], value)
            elif i == len(thresh) - 1:
                title = '> %g (%.3g%%)' % (thresh[i-1], value)
            else:
                title = '%g .. %g (%.3g%%)' % (thresh[i-1], thresh[i], value)
            if self.gnuplot_version >= 4.4:
                result += u'"%s" using 1:2:3:4:5 title "%s" with circles lc %s' % (
                    dat_file, title, colour[i % len(colour)])
            else:
                result += u'"%s" using 1:2 title "%s" with filledcurve lt %s' % (
                    dat_file, title, colour[i % len(colour)])
            if i > 0:
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
        return RosePlotter(context, args[1]).do_plot(args[2], args[3])


if __name__ == "__main__":
    sys.exit(main())
