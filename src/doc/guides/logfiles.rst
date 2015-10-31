.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2015  pywws contributors

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; either version 2
   of the License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

Understanding pywws log files
=============================

The pywws software uses Python's logging system to report errors, warnings and information that may be useful in diagnosing problems.
When you run the software interactively these messages are sent to your terminal window, when running a daemon process or cron job they should be written to a log file.

This document explains some of the pywws logging messages.
It's not a complete guide, and the messages you see will depend on your weather station and configuration, but it should help you understand some of the more common ones.

Many pywws commands have a ``-v`` or ``--verbose`` option to increase the verbosity of the logging messages.
This option can be repeated for even more verbosity, which may be useful when trying to diagnose a particular fault.

Here are some typical logging outputs.
The first shows pywws being run interactively:

.. code-block:: none
   :linenos:

   jim@firefly ~ $ pywws-livelog -v ~/weather/data/
   08:50:43:pywws.Logger:pywws version 15.07.1.dev1308
   08:50:43:pywws.Logger:Python version 2.7.3 (default, Mar 18 2014, 05:13:23) [GCC 4.6.3]
   08:50:44:pywws.WeatherStation.CUSBDrive:using pywws.device_libusb1
   08:50:49:pywws.Calib:Using user calibration
   08:50:49:pywws.Tasks.RegularTasks:Starting asynchronous thread
   08:51:05:pywws.ToService(wetterarchivde):1 records sent
   08:51:06:pywws.ToService(underground_rf):1 records sent
   08:51:06:pywws.ToService(cwop):1 records sent
   08:51:52:pywws.ToService(wetterarchivde):1 records sent
   08:51:52:pywws.ToService(underground_rf):1 records sent
   08:52:40:pywws.ToService(wetterarchivde):1 records sent
   08:52:40:pywws.ToService(underground_rf):1 records sent
   08:53:28:pywws.ToService(wetterarchivde):1 records sent
   08:53:28:pywws.ToService(underground_rf):1 records sent

Note that each line begins with a time stamp, in local time.
Line 1 is the command used to start pywws.
Line 2 shows the pywws version.
Line 3 shows the Python version.
Line 4 shows which Python USB library is being used.
Line 5 shows that a :py:mod:`"user calibration" <pywws.calib>` routine is being used.
Line 6 shows that a separate thread is being started to handle uploads (see :ref:`weather_ini-config`).
The remaining lines show uploads to various weather "services" (see :doc:`integration`).
You can see from the time stamps that they happen at 48 second intervals.

When running pywws as a daemon process the logging is less verbose:

.. code-block:: none
   :linenos:

   2015-07-20 10:46:00:pywws.Logger:pywws version 15.07.1.dev1308
   2015-07-20 10:50:06:pywws.weather_station:live_data log extended
   2015-07-20 16:25:59:pywws.weather_station:setting station clock 59.637
   2015-07-20 16:25:59:pywws.weather_station:station clock drift -0.461377 -0.296364
   2015-07-20 16:30:24:pywws.ToService(wetterarchivde):<urlopen error [Errno -2] Name or service not known>
   2015-07-20 16:30:24:pywws.ToService(underground_rf):<urlopen error [Errno -2] Name or service not known>
   2015-07-20 23:01:16:pywws.ToService(openweathermap):<urlopen error [Errno -2] Name or service not known>
   2015-07-21 01:14:18:pywws.weather_station:setting sensor clock 42.6678
   2015-07-21 01:14:18:pywws.weather_station:sensor clock drift -2.03116 -1.98475
   2015-07-21 09:00:47:pywws.ToTwitter:('Connection aborted.', gaierror(-2, 'Name or service not known'))
   2015-07-21 09:00:55:pywws.Upload:[Errno -2] Name or service not known
   2015-07-21 09:01:05:pywws.ToService(cwop):[Errno -3] Temporary failure in name resolution
   2015-07-21 09:06:05:pywws.ToService(underground):<urlopen error [Errno -2] Name or service not known>
   2015-07-21 09:06:05:pywws.ToService(metoffice):<urlopen error [Errno -2] Name or service not known>
   2015-07-21 16:30:59:pywws.weather_station:setting station clock 59.4771
   2015-07-21 16:30:59:pywws.weather_station:station clock drift -0.159373 -0.262116

Each line begins with a date and time stamp, in local time.
Line 1 shows the pywws version.
The remaining lines show normal status messages that are described below.

Clock drift
-----------

.. code-block:: none

   2015-08-31 20:10:45:pywws.weather_station:setting station clock 45.7137
   2015-08-31 20:10:45:pywws.weather_station:station clock drift -0.0171086 -0.313699
   2015-09-01 01:54:59:pywws.weather_station:setting sensor clock 35.2755
   2015-09-01 01:54:59:pywws.weather_station:sensor clock drift -1.12118 -1.37694

These lines report how the weather station's internal ("station") and external ("sensor") clocks are drifting with respect to the computer's clock.
These measurements are used to avoid accessing the station's USB port at the same time as it is receiving data or logging data, as this is known to cause some station's USB ports to become inaccessible.
The two "drift" figures are the current value (only accurate to about 1 second) and the long term average.
You should ensure that the ``usb activity margin`` value in your :ref:`weather.ini file <weather_ini-config>` is at least 0.5 seconds greater than the absolute value of the long term drift of each clock.
Note that these drift values change with temperature.

The clock drifts are measured at approximately 24 hour intervals.
If pywws loses synchronisation with your station it will measure them again.
Doing this measurement increases the risk of causing a USB lockup, so if pywws often loses synchronisation you should try and find out why it's happening.

Network problems
----------------

Occasionally one or more of the services and web sites you upload data to may become unavailable.
This leads to error messages like these:

.. code-block:: none

  2015-08-03 04:19:49:pywws.ToService(underground_rf):[Errno 104] Connection reset by peer
  2015-08-03 04:49:27:pywws.ToService(underground_rf):<urlopen error [Errno -2] Name or service not known>
  2015-08-03 05:19:41:pywws.ToService(wetterarchivde):<urlopen error [Errno 101] Network is unreachable>
  2015-08-03 05:19:46:pywws.ToService(underground_rf):<urlopen error [Errno 101] Network is unreachable>
  2015-08-03 05:50:52:pywws.ToService(wetterarchivde):<urlopen error [Errno -2] Name or service not known>
  2015-08-03 05:50:52:pywws.ToService(underground_rf):<urlopen error [Errno -2] Name or service not known>

To avoid swamping the log files duplicate messages are not logged, so you cannot tell how long the network outage lasted from the log files.

Status
------

.. code-block:: none

   2015-09-01 21:50:21:pywws.weather_station:status {'unknown': 0, 'invalid_wind_dir': 2048, 'lost_connection': 64, 'rain_overflow': 0}

The raw weather station data includes some "status" bits.
If any of these bits is non-zero when pywws starts, or the status changes value when pywws is running, the status value is logged.
The most common problem is ``lost_connection``: the weather station console is not receiving data from the outside sensors.
Contact is often restored a few minutes later, but if not you may need to reset your weather station console by taking its batteries out.
The ``invalid_wind_dir`` bit indicates that the wind direction sensor value is missing or invalid.
The ``rain_overflow`` bit is set when the rain gauge counter has reached its maximum value and gone back to zero.

Please let me know if you ever get a non-zero value for ``unknown``, particularly if you are able to correlate it with some other event.
There are 6 bits of data in the status byte whose function is not yet known.

Log extended
------------

.. code-block:: none

   2015-08-10 08:25:59:pywws.weather_station:live_data log extended
   2015-08-10 08:41:59:pywws.weather_station:live_data log extended
   2015-08-10 08:57:59:pywws.weather_station:live_data log extended

This shows a curiosity in the weather station's internal processing.
As the internal and external sensors drift there comes a time when an external reading is expected at the same time as the station is due to log some data.
To avoid a clash the station delays logging by one minute.
As the external readings are at 48 second intervals this avoids the problem until 16 minutes later (with the normal 5 minute logging interval) when another one minute delay is needed.
Eventually the clocks drift apart and normal operation is resumed.

Rain reset
----------

.. code-block:: none

   2015-08-25 13:30:51:pywws.Process.HourAcc:2015-08-25 12:30:48 rain reset 1048.4 -> 1047.1
   2015-08-25 13:35:51:pywws.Process.HourAcc:2015-08-25 12:30:48 rain reset 1048.4 -> 1047.1
   2015-08-25 13:40:51:pywws.Process.HourAcc:2015-08-25 12:30:48 rain reset 1048.4 -> 1047.1

The raw rainfall data from the outside sensors is the total number of times the "see saw" has tipped since the external sensors were last reset (by a battery change, unless you do it quickly).
This number should only ever increase, so the :py:mod:`pywws.Process` module warns of any decrease in the value as it may indicate corrupted data that needs manually correcting.
The logging message includes the UTC time stamp of the problem data to help you find it.

Live data missed
----------------

.. code-block:: none
   :linenos:

   2015-10-30 04:48:19:pywws.ToService(underground_rf):1 records sent
   2015-10-30 04:49:07:pywws.ToService(underground_rf):1 records sent
   2015-10-30 04:49:56:pywws.weather_station:live_data missed
   2015-10-30 04:50:44:pywws.ToService(underground_rf):1 records sent
   2015-10-30 04:51:31:pywws.ToService(underground_rf):1 records sent

Line 3 indicate that pywws failed to capture live data.

There are two possible causes. One is that a new data record is identical to the previous one so pywws doesn't detect a change. This is unlikely to happen if you are receiving wind data properly.

The more likely reason is that processing the previous record took so long that the next one arrived when pywws wasn't ready for it. "Processing" can include uploading to the Internet which is often prone to delays.  A solution to this is to set "asynchronous" to True in weather.ini. This uses a separate thread to do the uploading.

You may run with higher verbosity to get more information.  The "pause" values should indicate how soon it's ready for the next data.

Note that this is just an occasional missing "live" record though, so if it does not happen often you shouldn't worry too much about it.

"Live log" synchronisation
--------------------------

If you run pywws at a high verbosity you may see messages like the following:

.. code-block:: none
   :linenos:

   10:26:05:pywws.Logger:pywws version 15.07.0.dev1307
   10:26:05:pywws.Logger:Python version 2.7.8 (default, Sep 30 2014, 15:34:38) [GCC]
   10:26:05:pywws.WeatherStation.CUSBDrive:using pywws.device_libusb1
   10:26:06:pywws.Calib:Using user calibration
   10:26:06:pywws.Tasks.RegularTasks:Starting asynchronous thread
   10:26:06:pywws.weather_station:read period 5
   10:26:06:pywws.weather_station:delay 2, pause 0.5
   10:26:07:pywws.weather_station:delay 2, pause 0.5
   10:26:08:pywws.weather_station:delay 2, pause 0.5
   10:26:08:pywws.weather_station:delay 2, pause 0.5
   10:26:09:pywws.weather_station:delay 2, pause 0.5
   10:26:10:pywws.weather_station:delay 2, pause 0.5
   10:26:10:pywws.weather_station:delay 2, pause 0.5
   10:26:11:pywws.weather_station:delay 2, pause 0.5
   10:26:12:pywws.weather_station:delay 2, pause 0.5
   10:26:12:pywws.weather_station:delay 2, pause 0.5
   10:26:13:pywws.weather_station:delay 2, pause 0.5
   10:26:14:pywws.weather_station:delay 2, pause 0.5
   10:26:14:pywws.weather_station:live_data new data
   10:26:14:pywws.weather_station:setting sensor clock 38.7398
   10:26:14:pywws.weather_station:delay 3, pause 45.4993
   10:26:16:pywws.Tasks.RegularTasks:Doing asynchronous tasks
   10:27:00:pywws.weather_station:delay 3, pause 0.5
   10:27:00:pywws.weather_station:avoid 3.83538614245
   10:27:04:pywws.weather_station:live_data new data
   10:27:04:pywws.weather_station:delay 3, pause 43.3316
   10:27:06:pywws.Tasks.RegularTasks:Doing asynchronous tasks
   10:27:48:pywws.weather_station:delay 3, pause 0.5
   10:27:48:pywws.weather_station:avoid 3.79589626256
   10:27:52:pywws.weather_station:live_data new data
   10:27:52:pywws.weather_station:delay 4, pause 0.5
   10:27:53:pywws.weather_station:delay 4, pause 0.5
   10:27:54:pywws.weather_station:delay 4, pause 0.5
   10:27:54:pywws.weather_station:delay 4, pause 0.5
   10:27:54:pywws.Tasks.RegularTasks:Doing asynchronous tasks
   10:27:55:pywws.weather_station:delay 4, pause 0.5
   10:27:56:pywws.weather_station:delay 4, pause 0.5
   10:27:56:pywws.weather_station:delay 4, pause 0.5
   10:27:57:pywws.weather_station:delay 4, pause 0.5
   10:27:58:pywws.weather_station:delay 4, pause 0.5
   10:27:58:pywws.weather_station:delay 4, pause 0.5
   10:27:59:pywws.weather_station:delay 4, pause 0.5
   10:28:00:pywws.weather_station:delay 4, pause 0.5
   10:28:00:pywws.weather_station:delay 4, pause 0.5
   10:28:01:pywws.weather_station:delay 4, pause 0.5
   10:28:02:pywws.weather_station:delay 4, pause 0.5
   10:28:02:pywws.weather_station:delay 4, pause 0.5
   10:28:03:pywws.weather_station:delay 4, pause 0.5
   10:28:04:pywws.weather_station:delay 4, pause 0.5
   10:28:04:pywws.weather_station:delay 4, pause 0.5
   10:28:05:pywws.weather_station:delay 4, pause 0.5
   10:28:06:pywws.weather_station:delay 4, pause 0.5
   10:28:06:pywws.weather_station:delay 4, pause 0.5
   10:28:07:pywws.weather_station:live_data new ptr: 007320
   10:28:07:pywws.weather_station:setting station clock 7.43395
   10:28:07:pywws.weather_station:avoid 1.91954708099
   10:28:10:pywws.DataLogger:1 catchup records
   10:28:10:pywws.Process:Generating summary data
   10:28:10:pywws.Process:daily: 2015-08-31 21:00:00
   10:28:10:pywws.Process:monthly: 2015-07-31 21:00:00
   10:28:10:pywws.Process:monthly: 2015-08-31 21:00:00
   10:28:10:pywws.weather_station:delay 0, pause 26.121
   10:28:12:pywws.Tasks.RegularTasks:Doing asynchronous tasks

Line 6 shows that the weather station has the usual 5 minute logging interval.
Lines 7 to 18 show pywws waiting for the station to receive data from the outside sensors.
The ``delay`` value is the number of minutes since the station last logged some data.
The ``pause`` value is how many seconds pywws will wait before fetching data from the station again.
Lines 19 & 20 show new data being received and the "sensor" clock being set.
Line 21 shows that pywws now knows when data is next expected, so it can sleep for 43 seconds.
Line 22 shows the separate "upload" thread doing its processing while the main thread is sleeping.
Line 24 shows pywws avoiding USB activity around the time the station should receive external data.
Lines 31 to 53 show pywws waiting for the station to log data.
Lines 54 & 55 show the station logging some data and pywws using this to set the "station" clock.
The 6 digit number at the end of line 54 is the hexadecimal address where "live" data will now be written to, leaving data at the previous address as a "logged" value.
Lines 57 to 61 show pywws fetching logged data from the station and then processing it to produce the various summaries.

Crash with traceback
--------------------

Sometimes pywws software crashes.
When it does, the log file will often contain a traceback like this:

.. code-block:: none
   :linenos:

   18:50:57:pywws.LiveLog:error sending control message: Device or resource busy
   Traceback (most recent call last):
     File "/usr/local/lib/python2.7/dist-packages/pywws/LiveLog.py", line 80, in LiveLog
       logged_only=(not tasks.has_live_tasks())):
     File "/usr/local/lib/python2.7/dist-packages/pywws/LogData.py", line 256, in live_data
       for data, ptr, logged in self.ws.live_data(logged_only=logged_only):
     File "/usr/local/lib/python2.7/dist-packages/pywws/WeatherStation.py", line 446, in live_data
       new_ptr = self.current_pos()
     File "/usr/local/lib/python2.7/dist-packages/pywws/WeatherStation.py", line 585, in current_pos
       self._read_fixed_block(0x0020), self.lo_fix_format['current_pos'])
     File "/usr/local/lib/python2.7/dist-packages/pywws/WeatherStation.py", line 641, in _read_fixed_block
       result += self._read_block(mempos)
     File "/usr/local/lib/python2.7/dist-packages/pywws/WeatherStation.py", line 629, in _read_block
       new_block = self.cusb.read_block(ptr)
     File "/usr/local/lib/python2.7/dist-packages/pywws/WeatherStation.py", line 265, in read_block
       if not self.dev.write_data(buf):
     File "/usr/local/lib/python2.7/dist-packages/pywws/device_pyusb.py", line 152, in write_data
       usb.REQ_SET_CONFIGURATION, buf, value=0x200, timeout=50)
   USBError: error sending control message: Device or resource busy

Line 1 shows the exception that caused the crash.
Lines 3 to 18 show where in the program the problem happened.
Usually the last one is of interest, but the other function calls show how we got there.
Line 19 shows the full exception.
In this case it's a USBError raised by the pyusb library.
