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

"""Create text data file based on a template
::

%s

Introduction
------------

This is probably the most difficult to use module in the weather
station software collection. It generates text files based on a
"template" file plus the raw, hourly, daily & monthly weather station
data. The template processing goes beyond simple substitution of
values to include loops, jumps forwards or backwards in the data,
processing of the data and substitution of missing values.

A template file can be any sort of text file (plain text, xml, html,
etc.) to which "processing instructions" have been added. These
processing instructions are delimited by hash ('#') characters. They
are not copied to the output, but cause something else to happen:
either a data value is inserted or one of a limited number of other
actions is carried out.

Before writing your own template files, it might be useful to look at
some of the examples in the example_templates directory.

Text encoding
^^^^^^^^^^^^^

The ``[config]`` section of :ref:`weather.ini <weather_ini-config>` has
a ``template encoding`` entry that tells pywws what text encoding most
of your template files use. The default value, ``iso-8859-1``, is
suitable for most western European languages, but may need changing if
you use another language. It can be set to any text encoding recognised
by the Python :py:mod:`codecs` module.

Make sure your templates use the text encoding you set. The `iconv
<http://man7.org/linux/man-pages/man1/iconv.1.html>`_ program can be
used to transcode files.

.. versionadded:: 16.04.0
   the ``#encoding#`` processing instruction can be used to set the text
   encoding of a template file.

Processing instructions
-----------------------

Note that if the closing '#' of a processing instruction is the last
character on a line then the following line break is not outputted.
This makes templates easier to edit as you can have a separate line
for each processing instruction and still produce output with no line
breaks. If you want to output a line break after a processing
instruction, put a blank line immediately after it.

Processing instructions can be split across lines to improve
readability. Split lines are joined together before processing, after
removing any trailing newline characters.

``##``
^^^^^^

output a single '#' character.

``#! comment text#``
^^^^^^^^^^^^^^^^^^^^

a comment, no output generated. ``comment text`` can be any text
without a line break.

``#monthly#``
^^^^^^^^^^^^^

switch to "monthly" summary data. The index is reset to the most
recent value.

``#daily#``
^^^^^^^^^^^

switch to "daily" summary data. The index is reset to the most recent
value.

``#hourly#``
^^^^^^^^^^^^

switch to "hourly" summary data. The index is reset to the most recent
value.

``#raw#``
^^^^^^^^^

switch to "raw" data. The index is reset to the most recent value.

.. versionchanged:: 11.09
   This now selects "calibrated" data. The directive name remains
   unchanged for backwards compatibility.

``#live#``
^^^^^^^^^^

switch to "live" data. If the template is processed in the ``[live]``
section of ``weather.ini`` this will select the most up-to-date
weather data, otherwise it will have the same effect as ``#raw#``. Any
``#jump#`` will go to "raw" data.

``#timezone name#``
^^^^^^^^^^^^^^^^^^^

convert all datetime values to time zone ``name`` before output.
Permitted values for name are ``utc`` or ``local``.

``#locale expr#``
^^^^^^^^^^^^^^^^^

switch use of 'locale' on or off, according to ``expr``. When locale
is on floating point numbers may use a comma as the decimal separator
instead of a point, depending on your localisation settings. Use
``"True"`` or ``"False"`` for expr.

``#encoding expr#``
^^^^^^^^^^^^^^^^^^^

.. versionadded:: 16.04.0

set the template text encoding to ``expr``, e.g. ``ascii``, ``utf8`` or
``html``. The ``html`` encoding is a special case. It writes ``ascii``
files but with non ASCII characters converted to HTML entities.

Any ``#encoding#`` directive should be placed near the beginning of the
template file, before any non-ASCII characters are used.

``#roundtime expr#``
^^^^^^^^^^^^^^^^^^^^

switch time rounding on or off, according to ``expr``. When time
rounding is on, 30 seconds is added to each time value used. This is
useful if you are only printing out hours and minutes, e.g. with a
"%%H:%%M" format, and want time values such as 10:23:58 to appear as
"10:24". Use ``"True"`` or ``"False"`` for expr.

``#jump count#``
^^^^^^^^^^^^^^^^

jump ``count`` values. The data index is adjusted by ``count`` hours
or days. Negative values jump back in time.

It is a good idea to put jumps within a loop at the end, just before
the ``#endloop#`` instruction. The loop can then terminate cleanly if
it has run out of data.

``#goto date-time#``
^^^^^^^^^^^^^^^^^^^^

go to ``date-time``. The data index is adjusted to the record
immediately after ``date-time``. This can be in UTC or your local time
zone, according to the setting of ``timezone``, and must exactly match
the ISO date format, for example ``"2010-11-01 12:00:00"`` is noon on
1st November 2010.

Parts of ``date-time`` can be replaced with strftime style %% format
characters to specify the current loop index. For example,
``"%%Y-%%m-01 12:00:00"`` is noon on 1st of this month.

``#loop count#``
^^^^^^^^^^^^^^^^

start a loop that will repeat ``count`` times. ``count`` must be one
or more.

``#endloop#``
^^^^^^^^^^^^^

end a loop started by ``#loop count#``. The template processing will
go back to the line containing the ``#loop count#`` instruction. Don't
try to nest loops.

``#key fmt_string no_value_string conversion#``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

output a data value. ``key`` is the data key, e.g. ``temp_out`` for
outdoor temperature. ``fmt_string`` is a printf-like format string
(actually Python's %% operator) except for datetime values, when it is
input to datetime's ``strftime()`` method. ``no_value_string`` is
output instead of ``fmt_string`` when the data value is absent, e.g.
if the station lost contact with the outside sensor. ``conversion`` is
a Python expression to convert the data, e.g. to convert wind speed
from m/s to mph you could use ``"x * 3.6 / 1.609344"``, or the more
convenient provided function ``"wind_mph(x)"``. See the
:py:mod:`pywws.conversions` module for details of the available
functions.

All these values need double quotes " if they contain spaces or other
potentially difficult characters. All except ``key`` are optional, but
note that if you want to specify a conversion, you also need to
specify ``fmt_string`` and ``no_value_string``.

``#calc expression fmt_string no_value_string conversion#``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

output a value computed from one or more data items. ``expression`` is
any valid Python expression, e.g. ``"dew_point(data['temp_out'],
data['hum_out'])"`` to compute the outdoor dew point. ``fmt_string``,
``no_value_string`` and ``conversion`` are as described above. Note
that it is probably more efficient to incorporate any conversion into
expression.

In addition to the functions in the :py:mod:`pywws.conversions` module
there are four more useful functions: ``rain_hour(data)`` returns the
amount of rain in the last hour, ``rain_day(data)`` returns the amount
of rain since midnight (local time), ``rain_24hr(data)`` returns the
amount of rain in the last 24 hours, and ``hour_diff(data, key)``
returns the change in data item ``key`` over the last hour.

Example
-------

Here is an example snippet showing basic and advanced use of the
template features. It is part of the 6hrs.txt example template file,
which generates an HTML table of 7 hourly readings (which should span
6 hours). ::

  #hourly#
  #jump -6#
  #loop 7#
    <tr>
      <td>#idx "%%Y/%%m/%%d" "" "[None, x][x.hour == 0 or loop_count == 7]"#</td>
      <td>#idx "%%H%%M %%Z"#</td>
      <td>#temp_out "%%.1f °C"#</td>
      <td>#hum_out "%%d%%%%"#</td>
      <td>#wind_dir "%%s" "-" "winddir_text(x)"#</td>
      <td>#wind_ave "%%.0f mph" "" "wind_mph(x)"#</td>
      <td>#wind_gust "%%.0f mph" "" "wind_mph(x)"#</td>
      <td>#rain "%%0.1f mm"#</td>
      <td>#rel_pressure "%%.0f hPa"#, #pressure_trend "%%s" "" "pressure_trend_text(x)"#</td>
    </tr>
  #jump 1#
  #endloop#

The first three lines of this snippet do the following: select hourly
data, jump back 6 hours, start a loop with a count of 7. A jump
forward of one hour appears just before the end of the repeated
segment. As this last jump (of one hour) happens each time round the
loop, a sequence of 7 data readings will be output. The last line
marks the end of the loop — everything between the ``#loop 7#`` and
``#endloop#`` lines is output 7 times.

The ``#temp_out ...#``, ``#hum_out ...#``, ``#rain ...#`` and
``#rel_pressure ...#`` instructions show basic data output. They each
use a ``fmt_string`` to format the data appropriately. The ``#wind_ave
...#`` and ``#wind_gust ...#`` instructions show how to use a
conversion expression to convert m/s to mph.

The ``#wind_dir ...#`` and ``#pressure_trend ...#`` instructions show
use of the built-in functions ``winddir_text`` and
``pressure_trend_text`` to convert numerical values into text.

Finally we get to datetime values. The ``#idx "%%H%%M"#`` instruction
simply outputs the time (in HHMM format) of the data's index. The
``#idx "%%Y/%%m/%%d" "" "[None, x][x.hour == 0 or loop_count == 7]"#``
instruction is a bit more complicated. It outputs the date, but only
on the first line or if the date has changed. It does this by indexing
the array ``[None, x]`` with a boolean expression that is true when
``loop_count`` is 7 (i.e. on the first pass through the loop) or
``x.hour`` is zero (i.e. this is the first hour of the day).

Detailed API
------------

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.template [options] data_dir template_file output_file
 options are:
  --help    display this help
 data_dir is the root directory of the weather data
 template_file is the template text source file
 output_file is the name of the text file to be created
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

from ast import literal_eval
import codecs
from datetime import datetime, timedelta
import getopt
import locale
import logging
import os
import shlex
import sys

from pywws.constants import HOUR, SECOND, DAY
from pywws import conversions
from pywws.conversions import *
from pywws.forecast import zambretti, zambretti_code
import pywws.localisation
import pywws.logger
import pywws.storage
from pywws.timezone import time_zone
import pywws.weatherstation

logger = logging.getLogger(__name__)

# aliases for compatibility with old templates
Zambretti = zambretti
ZambrettiCode = zambretti_code


class Computations(object):
    def __init__(self, context):
        self.context = context

    def hour_diff(self, data, key):
        calib_data = self.context.calib_data
        hour_ago = calib_data[calib_data.nearest(data['idx'] - HOUR)]
        return data[key] - hour_ago[key]

    def rain_hour(self, data):
        return max(0.0, self.hour_diff(data, 'rain'))

    def rain_day(self, data):
        calib_data = self.context.calib_data
        midnight = time_zone.utc_to_local(data['idx'])
        midnight = midnight.replace(hour=0, minute=0, second=0)
        midnight = time_zone.local_to_utc(midnight)
        midnight_data = calib_data[calib_data.nearest(midnight)]
        return max(0.0, data['rain'] - midnight_data['rain'])

    def rain_24hr(self, data):
        calib_data = self.context.calib_data
        day_ago = calib_data[calib_data.nearest(data['idx'] - DAY)]
        return max(0.0, data['rain'] - day_ago['rain'])


class Template(object):
    def __init__(self, context, use_locale=True):
        self.params = context.params
        self.status = context.status
        self.calib_data = context.calib_data
        self.hourly_data = context.hourly_data
        self.daily_data = context.daily_data
        self.monthly_data = context.monthly_data
        self.use_locale = use_locale
        self.computations = Computations(context)

    def process(self, live_data, template_file):
        def jump(idx, count):
            while count > 0:
                new_idx = data_set.after(idx + SECOND)
                if new_idx == None:
                    break
                idx = new_idx
                count -= 1
            while count < 0:
                new_idx = data_set.before(idx)
                if new_idx == None:
                    break
                idx = new_idx
                count += 1
            return idx, count == 0

        params = self.params
        if not live_data:
            idx = self.calib_data.before(datetime.max)
            if not idx:
                logger.error("No calib data - run pywws.process first")
                return
            live_data = self.calib_data[idx]
        # get default character encoding of template input & output files
        self.encoding = params.get('config', 'template encoding', 'iso-8859-1')
        file_encoding = self.encoding
        if file_encoding == 'html':
            file_encoding = 'ascii'
        # get conversions module to create its 'private' wind dir text
        # array, then copy it to deprecated wind_dir_text variable
        winddir_text(0)
        wind_dir_text = conversions._winddir_text_array
        hour_diff = self.computations.hour_diff
        rain_hour = self.computations.rain_hour
        rain_day = self.computations.rain_day
        rain_24hr = self.computations.rain_24hr
        pressure_offset = float(self.params.get('config', 'pressure offset'))
        fixed_block = literal_eval(self.status.get('fixed', 'fixed block'))
        # start off with no time rounding
        round_time = None
        # start off in hourly data mode
        data_set = self.hourly_data
        # start off in utc
        local_time = False
        # start off with default use_locale setting
        use_locale = self.use_locale
        # jump to last item
        idx, valid_data = jump(datetime.max, -1)
        if not valid_data:
            logger.error("No summary data - run pywws.process first")
            return
        data = data_set[idx]
        # open template file, if not already a file(like) object
        if hasattr(template_file, 'readline'):
            tmplt = template_file
        else:
            tmplt = open(template_file, 'rb')
        # do the text processing
        line = ''
        while True:
            new_line = tmplt.readline()
            if not new_line:
                break
            if isinstance(new_line, bytes) or sys.version_info[0] < 3:
                new_line = new_line.decode(file_encoding)
            line += new_line
            parts = line.split('#')
            if len(parts) % 2 == 0:
                # odd number of '#'
                line = line.rstrip('\r\n')
                continue
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # not a processing directive
                    if i == 0 or part != '\n':
                        yield part
                    continue
                if part and part[0] == '!':
                    # comment
                    continue
                # Python 2 shlex can't handle unicode
                if sys.version_info[0] < 3:
                    part = part.encode(file_encoding)
                command = shlex.split(part)
                if sys.version_info[0] < 3:
                    command = map(lambda x: x.decode(file_encoding), command)
                if command == []:
                    # empty command == print a single '#'
                    yield u'#'
                elif command[0] in list(data.keys()) + ['calc']:
                    # output a value
                    if not valid_data:
                        continue
                    # format is: key fmt_string no_value_string conversion
                    # get value
                    if command[0] == 'calc':
                        x = eval(command[1])
                        del command[1]
                    else:
                        x = data[command[0]]
                    # adjust time
                    if isinstance(x, datetime):
                        if round_time:
                            x += round_time
                        if local_time:
                            x = time_zone.utc_to_local(x)
                        else:
                            x = x.replace(tzinfo=time_zone.utc)
                    # convert data
                    if x is not None and len(command) > 3:
                        x = eval(command[3])
                    # get format
                    fmt = u'%s'
                    if len(command) > 1:
                        fmt = command[1]
                    # write output
                    if x is None:
                        if len(command) > 2:
                            yield command[2]
                    elif isinstance(x, datetime):
                        if sys.version_info[0] < 3:
                            fmt = fmt.encode(file_encoding)
                        x = x.strftime(fmt)
                        if sys.version_info[0] < 3:
                            if self.encoding == 'html':
                                x = x.decode('ascii', errors='xmlcharrefreplace')
                            else:
                                x = x.decode(file_encoding)
                        yield x
                    elif not use_locale:
                        yield fmt % (x)
                    elif sys.version_info >= (2, 7) or '%%' not in fmt:
                        yield locale.format_string(fmt, x)
                    else:
                        yield locale.format_string(
                            fmt.replace('%%', '##'), x).replace('##', '%')
                elif command[0] == 'monthly':
                    data_set = self.monthly_data
                    idx, valid_data = jump(datetime.max, -1)
                    data = data_set[idx]
                elif command[0] == 'daily':
                    data_set = self.daily_data
                    idx, valid_data = jump(datetime.max, -1)
                    data = data_set[idx]
                elif command[0] == 'hourly':
                    data_set = self.hourly_data
                    idx, valid_data = jump(datetime.max, -1)
                    data = data_set[idx]
                elif command[0] == 'raw':
                    data_set = self.calib_data
                    idx, valid_data = jump(datetime.max, -1)
                    data = data_set[idx]
                elif command[0] == 'live':
                    data_set = self.calib_data
                    idx = live_data['idx']
                    valid_data = True
                    data = live_data
                elif command[0] == 'timezone':
                    if command[1] == 'utc':
                        local_time = False
                    elif command[1] == 'local':
                        local_time = True
                    else:
                        logger.error("Unknown time zone: %s", command[1])
                        return
                elif command[0] == 'locale':
                    use_locale = eval(command[1])
                elif command[0] == 'encoding':
                    self.encoding = command[1]
                    file_encoding = self.encoding
                    if file_encoding == 'html':
                        file_encoding = 'ascii'
                elif command[0] == 'roundtime':
                    if eval(command[1]):
                        round_time = timedelta(seconds=30)
                    else:
                        round_time = None
                elif command[0] == 'jump':
                    prevdata = data
                    idx, valid_data = jump(idx, int(command[1]))
                    data = data_set[idx]
                elif command[0] == 'goto':
                    prevdata = data
                    time_str = command[1]
                    if '%' in time_str:
                        if local_time:
                            lcl = time_zone.utc_to_local(idx)
                        else:
                            lcl = idx.replace(tzinfo=time_zone.utc)
                        time_str = lcl.strftime(time_str)
                    new_idx = pywws.weatherstation.WSDateTime.from_csv(time_str)
                    if local_time:
                        new_idx = time_zone.local_to_utc(new_idx)
                    new_idx = data_set.after(new_idx)
                    if new_idx:
                        idx = new_idx
                        data = data_set[idx]
                        valid_data = True
                    else:
                        valid_data = False
                elif command[0] == 'loop':
                    loop_count = int(command[1])
                    loop_start = tmplt.tell()
                elif command[0] == 'endloop':
                    loop_count -= 1
                    if valid_data and loop_count > 0:
                        tmplt.seek(loop_start, 0)
                else:
                    logger.error("Unknown processing directive: #%s#", part)
                    return
            line = ''

    def make_text(self, template_file, live_data=None):
        result = u''
        for text in self.process(live_data, template_file):
            result += text
        return result

    def make_file(self, template_file, output_file, live_data=None):
        text = self.make_text(template_file, live_data)
        if self.encoding == 'html':
            kwds = {'encoding': 'ascii', 'errors': 'xmlcharrefreplace'}
        else:
            kwds = {'encoding': self.encoding}
        with codecs.open(output_file, 'w', **kwds) as of:
            of.write(text)
        return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "", ['help'])
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 1
    # check arguments
    if len(args) != 3:
        print('Error: 3 arguments required\n', file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 2
    # process options
    for o, a in opts:
        if o == '--help':
            print(__usage__.strip())
            return 0
    pywws.logger.setup_handler(1)
    with pywws.storage.pywws_context(args[0]) as context:
        pywws.localisation.set_application_language(context.params)
        return Template(context).make_file(args[1], args[2])


if __name__ == "__main__":
    sys.exit(main())
