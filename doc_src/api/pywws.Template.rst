pywws.Template
==============

Introduction
------------

This is probably the most difficult to use module in the weather station software collection. It generates text files based on a "template" file plus the raw, hourly, daily & monthly weather station data. The template processing goes beyond simple substitution of values to include loops, jumps forwards or backwards in the data, processing of the data and substitution of missing values.

A template file can be any sort of text file (plain text, xml, html, etc.) to which "processing instructions" have been added. These processing instructions are delimited by hash ('#') characters. They are not copied to the output, but cause something else to happen: either a data value is inserted or one of a limited number of other actions is carried out.

Before writing your own template files, it might be useful to look at some of the examples in the example_templates directory.

Processing instructions
-----------------------

  * ``##``: output a single '#' character.
  * ``#monthly#``: switch to "monthly" summary data. The index is reset to the most recent value.
  * ``#daily#``: switch to "daily" summary data. The index is reset to the most recent value.
  * ``#hourly#``: switch to "hourly" summary data. The index is reset to the most recent value.
  * ``#raw#``: switch to "raw" data. The index is reset to the most recent value.
  * ``#timezone name#``: convert all datetime values to time zone ``name`` before output. Permitted values for name are ``utc`` or ``local``.
  * ``#roundtime expr#``: switch time rounding on or off, according to ``expr``. When time rounding is on, 30 seconds is added to each time value used. This is useful if you are only printing out hours and minutes, e.g. with a "%H:%M" format, and want time values such as 10:23:58 to appear as "10:24". Use ``"True"`` or ``"False"`` for expr.
  * ``#jump count#``: jump ``count`` values. The data index is adjusted by ``count`` hours or days. Negative values jump back in time.

    It is a good idea to put jumps within a loop at the end, just before the ``#endloop#`` instruction. The loop can then terminate cleanly if it has run out of data.
  * ``#goto date-time#``: go to ``date-time``. The data index is adjusted to the record immediately after ``date-time``. This can be in UTC or your local time zone, according to the setting of ``timezone``, and must exactly match the ISO date format, for example ``"2010-11-01 12:00:00"`` is noon on 1st November 2010.

    Parts of ``date-time`` can be replaced with strftime style % format characters to specify the current loop index. For example, ``"%Y-%m-01 12:00:00"`` is noon on 1st of this month.
  * ``#loop count#``: start a loop that will repeat ``count`` times. ``count`` must be one or more.
  * ``#endloop#``: end a loop started by ``#loop count#``. The template processing will go back to the line containing the ``#loop count#`` instruction. Don't try to nest loops.
  * ``#key fmt_string no_value_string conversion#``: output a data value. ``key`` is the data key, e.g. ``temp_out`` for outdoor temperature. ``fmt_string`` is a printf-like format string (actually Python's % operator) except for datetime values, when it is input to datetime's ``strftime()`` method. ``no_value_string`` is output instead of ``fmt_string`` when the data value is absent, e.g. if the station lost contact with the outside sensor. ``conversion`` is a Python expression to convert the data, e.g. to convert wind speed from m/s to mph you could use ``"x * 3.6 / 1.609344"``.

    All these values need double quotes " if they contain spaces or other potentially difficult characters. All except ``key`` are optional, but note that if you want to specify a conversion, you also need to specify ``fmt_string`` and ``no_value_string``.
  * ``#calc expression fmt_string no_value_string conversion#``: output a value computed from one or more data items. ``expression`` is any valid Python expression, e.g. ``"dew_point(data['temp_out'], data['hum_out'])"`` to compute the outdoor dew point. ``fmt_string``, ``no_value_string`` and ``conversion`` are as described above. Note that it is probably more efficient to incorporate any conversion into expression.

Example
-------

Here is an example snippet showing basic and advanced use of the template features. It is part of the 6hrs.txt example template file, which generates an HTML table of 7 hourly readings (which should span 6 hours). ::

  #hourly#
  #jump -6#
  #loop 7#
    <tr>
      <td>#idx "%Y/%m/%d" "" "[None, x][x.hour == 0 or loop_count == 7]"#</td>
      <td>#idx "%H%M %Z"#</td>
      <td>#temp_out "%.1f °C"#</td>
      <td>#hum_out "%d%%"#</td>
      <td>#wind_dir "%s" "-" "wind_dir_text[x]"#</td>
      <td>#wind_ave "%.0f mph" "" "x * 3.6 / 1.609344"#</td>
      <td>#wind_gust "%.0f mph" "" "x * 3.6 / 1.609344"#</td>
      <td>#rain "%0.1f mm"#</td>
      <td>#rel_pressure "%.0f hPa"#, #pressure_trend "%s" "" "pressure_trend_text(x)"#</td>
    </tr>
  #jump 1#
  #endloop#

The first three lines of this snippet do the following: select hourly data, jump back 6 hours, start a loop with a count of 7. A jump forward of one hour appears just before the end of the repeated segment. As this last jump (of one hour) happens each time round the loop, a sequence of 7 data readings will be output. The last line marks the end of the loop — everything between the ``#loop 7#`` and ``#endloop#`` lines is output 7 times.

The ``#temp_out ...#``, ``#hum_out ...#``, ``#rain ...#`` and ``#rel_pressure ...#`` instructions show basic data output. They each use a ``fmt_string`` to format the data appropriately. The ``#wind_ave ...#`` and ``#wind_gust ...#`` instructions show how to use a conversion expression to convert m/s to mph.

The ``#wind_dir ...#`` and ``#pressure_trend ...#`` instructions show use of the built-in array ``wind_dir_text`` and function ``pressure_trend_text`` to convert numerical values into English text.

Finally we get to datetime values. The ``#idx "%H%M"#`` instruction simply outputs the time (in HHMM format) of the data's index. The ``#idx "%Y/%m/%d" "" "[None, x][x.hour == 0 or loop_count == 7]"#`` instruction is a bit more complicated. It outputs the date, but only on the first line or if the date has changed. It does this by indexing the array ``[None, x]`` with a boolean expression that is true when ``loop_count`` is 7 (i.e. on the first pass through the loop) or ``x.hour`` is zero (i.e. this is the first hour of the day).

Detailed API
------------

.. automodule:: pywws.Template

   .. rubric:: Functions

   .. autosummary::
   
      main
   
   .. rubric:: Classes

   .. autosummary::
   
      Template
