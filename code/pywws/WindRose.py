#!/usr/bin/env python

"""Plot a "wind rose"

::

%s

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python RunModule.py WindRose [options] data_dir temp_dir xml_file output_file
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

from .conversions import (
    illuminance_wm2, pressure_inhg, rain_inch, temp_f,
    winddir_degrees, winddir_text, wind_kmph, wind_mph, wind_kn, wind_bft)
from . import DataStore
from . import Localisation
from .Plot import BasePlotter
from .TimeZone import Local
from .WeatherStation import dew_point

class RosePlotter(BasePlotter):
    def GetPlotList(self):
        return self.GetChildren(self.graph, 'windrose')
    def GetDefaultRows(self):
        return int(math.sqrt(self.plot_count))
    def GetDefaultPlotSize(self):
        return 600 // self.rows, 600 // self.rows
    def GetPreamble(self):
        result = """set polar
set angles degrees
set xtics axis nomirror
set ytics axis nomirror
set zeroaxis
set grid polar 22.5
set size square
unset border
"""
        lmargin = eval(self.GetValue(self.graph, 'lmargin', '-1'))
        result += 'set lmargin %g\n' % (lmargin)
        lmargin = eval(self.GetValue(self.graph, 'rmargin', '-1'))
        result += 'set rmargin %g\n' % (lmargin)
        lmargin = eval(self.GetValue(self.graph, 'tmargin', '-1'))
        result += 'set tmargin %g\n' % (lmargin)
        lmargin = eval(self.GetValue(self.graph, 'bmargin', '-1'))
        result += 'set bmargin %g\n' % (lmargin)
        return result
    def PlotData(self, plot_no, plot, source):
        _ = Localisation.translation.ugettext
        # get statistics
        thresh = eval(self.GetValue(
            plot, 'threshold', '0.0, 1.54, 3.09, 5.14, 8.23, 10.8, 15.5'))
        thresh = thresh + (1000.0,)
        colour = eval(self.GetValue(plot, 'colour', str(range(len(thresh)))))
        xcalc = self.GetValue(plot, 'xcalc', 'True')
        xcalc = compile(xcalc, '<string>', 'eval')
        ycalc = self.GetValue(plot, 'ycalc', None)
        ycalc = compile(ycalc, '<string>', 'eval')
        histograms = []
        for i in range(len(thresh)):
            hist = []
            for n in range(16):
                hist.append(0)
            histograms.append(hist)
        # x_lo & x_hi are in local time, data is indexed in UTC
        start = self.x_lo - self.utcoffset
        stop = self.x_hi - self.utcoffset
        stop = stop + timedelta(minutes=1)
        for data in source[start:stop]:
            wind_dir = data['wind_dir']
            if wind_dir == None or wind_dir >= 16:
                continue
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
            histograms[0][n] = total // 16
        # integrate histograms
        for i in range(1, len(thresh)):
            for n in range(16):
                histograms[i][n] += histograms[i-1][n]
        total = 0
        for n in range(16):
            total += histograms[-1][n]
        result = ''
        yrange = self.GetValue(plot, 'yrange', '31')
        if yrange == '*':
            # auto-ranging
            if total > 0:
                max_petal = 100.0 * float(max(histograms[-1])) / float(total)
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
        result += 'set xrange [-%d:%d]\n' % (yrange, yrange)
        result += 'set yrange [-%d:%d]\n' % (yrange, yrange)
        points = [_('N'), _('S'), _('E'), _('W')]
        points = eval(self.GetValue(plot, 'points', str(points)))
        result += 'set label 1000 "%s" at 0, %d center front\n' % (points[0], yrange)
        result += 'set label 1001 "%s" at 0, -%d center front\n' % (points[1], yrange)
        result += 'set label 1002 "%s" at %d, 0 center front\n' % (points[2], yrange)
        result += 'set label 1003 "%s" at -%d, 0 center front\n' % (points[3], yrange)
        # plot segments for each speed-direction
        result += 'plot '
        for i in reversed(range(len(thresh))):
            dat_file = os.path.join(self.work_dir, 'plot_%d_%d.dat' % (plot_no, i))
            self.tmp_files.append(dat_file)
            dat = open(dat_file, 'w')
            sub_total = 0
            for n in range(16):
                angle = 90.0 - (n * 22.5)
                sub_total += histograms[i][n]
                if i > 0:
                    sub_total -= histograms[i-1][n]
                if total > 0:
                    value = 100.0 * float(histograms[i][n]) / float(total)
                else:
                    value = 0.0
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
            result += '"%s" using 1:2 title "%s" with filledcurve lt %d' % (
                dat_file, title, colour[i % len(colour)])
            if i > 0:
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
    Localisation.SetApplicationLanguage(params)
    return RosePlotter(
        params,
        DataStore.calib_store(args[0]), DataStore.hourly_store(args[0]),
        DataStore.daily_store(args[0]), DataStore.monthly_store(args[0]),
        args[1]
        ).DoPlot(args[2], args[3])
if __name__ == "__main__":
    sys.exit(main())
