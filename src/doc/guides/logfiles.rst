.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2015-18  pywws contributors

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

   jim@gordon:~ $ pywws-livelog -v ~/weather/data/
   09:25:11:pywws.logger:pywws version 18.5.0, build 1541 (d505b50)
   09:25:11:pywws.logger:Python version 3.5.3 (default, Jan 19 2017, 14:11:04) [GCC 6.3.0 20170124]
   09:25:12:pywws.weatherstation:using pywws.device_libusb1
   09:25:17:pywws.calib:Using user calibration
   09:25:46:pywws.weatherstation:status {'rain_overflow': False, 'lost_connection': False}
   09:25:53:pywws.regulartasks:doing task sections ['live']
   09:25:54:pywws.service.openweathermap:OK
   09:25:54:pywws.service.openweathermap:1 record sent
   09:25:55:pywws.service.underground:server response "success"
   09:25:55:pywws.service.underground:1 record sent
   09:26:41:pywws.regulartasks:doing task sections ['live']
   09:26:42:pywws.service.openweathermap:1 record sent
   09:26:44:pywws.service.underground:1 record sent
   09:27:29:pywws.regulartasks:doing task sections ['live']
   09:27:30:pywws.service.openweathermap:1 record sent
   09:27:33:pywws.service.underground:1 record sent
   09:28:17:pywws.regulartasks:doing task sections ['live']
   09:28:19:pywws.service.openweathermap:1 record sent
   09:28:22:pywws.service.underground:1 record sent
   09:29:05:pywws.regulartasks:doing task sections ['live']
   09:29:07:pywws.service.openweathermap:1 record sent
   09:29:07:pywws.service.underground:1 record sent
   09:29:16:pywws.weatherstation:live_data new ptr: 0053a0
   09:29:16:pywws.process:Generating summary data
   09:29:17:pywws.regulartasks:doing task sections ['logged']
   09:29:17:pywws.service.wetterarchivde:server response "{'version': '6.0', 'status': 'SUCCESS'}"
   09:29:17:pywws.service.wetterarchivde:1 record sent
   09:29:17:pywws.service.cwop:OK
   09:29:17:pywws.service.cwop:1 record sent
   09:29:20:pywws.service.metoffice:OK
   09:29:20:pywws.service.metoffice:1 record sent

Note that each line begins with a time stamp, in local time.
Line 1 is the command used to start pywws.
Line 2 shows the pywws version.
Line 3 shows the Python version.
Line 4 shows which Python USB library is being used.
Line 5 shows that a :py:mod:`"user calibration" <pywws.calib>` routine is being used.
Line 6 shows the current value of the weather station "status" bits.
This will be shown again if the status changes.
Lines 7, 12, 15, 18 & 21 show that tasks in the ``[live]`` section of ``weather.ini`` are being executed.
You can see from the time stamps that they happen at 48 second intervals.
Line 24 shows that the station has "logged" data and moved on to the next memory address.
pywws then generates summary data and executes tasks in the ``[logged]`` section of ``weather.ini``.

The remaining lines show uploads to various weather "services" (see :doc:`integration`).
Uploads to ``openweathermap`` and ``underground`` are done every 48 seconds.
Uploads to ``wetterarchivde``, ``cwop``, and ``metoffice`` are less frequent.
The first upload to a service logs ``OK`` or a message from the server.
This is not shown again unless the response changes.

When running pywws as a daemon process the logging is less verbose:

.. code-block:: none

   2018-05-27 10:50:40:pywws.logger:pywws version 18.5.0, build 1541 (d505b50)
   2018-05-27 10:51:19:pywws.weatherstation:status {'lost_connection': False, 'rain_overflow': False}
   2018-05-27 10:54:19:pywws.service.cwop:1 record(s) dropped
   2018-05-27 10:54:19:pywws.service.cwop:OK
   2018-05-27 10:54:19:pywws.service.wetterarchivde:server response "{'version': '6.0', 'status': 'SUCCESS'}"
   2018-05-27 10:54:19:pywws.service.wetterarchivde:2 records sent
   2018-05-27 10:54:20:pywws.service.openweathermap:OK
   2018-05-27 10:54:20:pywws.service.openweathermap:2 records sent
   2018-05-27 10:54:20:pywws.service.underground:server response "success"
   2018-05-27 10:54:20:pywws.service.metoffice:OK
   2018-05-27 10:54:20:pywws.service.underground:2 records sent
   2018-05-27 10:54:21:pywws.service.metoffice:2 records sent
   2018-05-27 11:00:31:pywws.towebsite:OK
   2018-05-27 11:00:33:pywws.totwitter:OK
   2018-05-27 11:54:14:pywws.weatherstation:setting station clock 14.371
   2018-05-27 11:54:14:pywws.weatherstation:station clock drift -0.499934 -0.401405
   2018-05-27 14:00:36:pywws.towebsite:[Errno 111] Connection refused
   2018-05-27 14:01:16:pywws.towebsite:OK
   2018-05-27 15:00:34:pywws.towebsite:[Errno 111] Connection refused
   2018-05-27 15:17:25:pywws.towebsite:[Errno 110] Connection timed out
   2018-05-27 15:18:05:pywws.towebsite:OK
   2018-05-28 01:05:47:pywws.weatherstation:setting sensor clock 11.1295
   2018-05-28 01:05:47:pywws.weatherstation:sensor clock drift 1.02042 0.987513
   2018-05-28 01:10:29:pywws.service.metoffice:HTTPConnectionPool(host='wow.metoffice.gov.uk', port=80): Read timed out. (read timeout=60)
   2018-05-28 01:11:09:pywws.service.metoffice:repeated data 2018-05-28 00:09:14
   2018-05-28 01:14:25:pywws.service.metoffice:OK
   2018-05-28 01:50:31:pywws.service.metoffice:HTTPConnectionPool(host='wow.metoffice.gov.uk', port=80): Read timed out. (read timeout=60)
   2018-05-28 01:52:52:pywws.service.metoffice:repeated data 2018-05-28 00:49:14
   2018-05-28 01:55:22:pywws.service.metoffice:HTTPConnectionPool(host='wow.metoffice.gov.uk', port=80): Read timed out. (read timeout=60)
   2018-05-28 01:57:42:pywws.service.metoffice:OK
   2018-05-28 09:00:38:pywws.totwitter:2 records sent
   2018-05-28 10:50:07:pywws.service.metoffice:HTTPConnectionPool(host='wow.metoffice.gov.uk', port=80): Read timed out. (read timeout=60)
   2018-05-28 10:50:47:pywws.service.metoffice:OK
   2018-05-28 11:59:14:pywws.weatherstation:setting station clock 14.0721
   2018-05-28 11:59:14:pywws.weatherstation:station clock drift -0.297843 -0.375514
   2018-05-28 19:44:20:pywws.weatherstation:live_data log extended

Each line begins with a date and time stamp, in local time.
Because pywws hadn't been run for 10 minutes each service starts by uploading 2 "catchup" records, except ``cwop`` which only accepts live data so one record is dropped.
At 11:00 am the first ``[hourly]`` tasks are run, uploading to a website and sending to Twitter.
The 14:00 and 15:00 website uploads failed, but were successful later on.

The ``metoffice`` upload at 01:10:29 appeared to fail, but when it was retried at 01:11:09 the server said it already had the data.
(Note the data timestamp is in UTC, the log message time stamp is in BST, one hour ahead.)

The remaining lines show status messages that are described in more detail below.

Clock drift
-----------

.. code-block:: none

   2018-05-28 01:05:47:pywws.weatherstation:setting sensor clock 11.1295
   2018-05-28 01:05:47:pywws.weatherstation:sensor clock drift 1.02042 0.987513

   2018-05-28 11:59:14:pywws.weatherstation:setting station clock 14.0721
   2018-05-28 11:59:14:pywws.weatherstation:station clock drift -0.297843 -0.375514

These lines report how the weather station's internal ("station") and external ("sensor") clocks are drifting with respect to the computer's clock.
(The ``3080`` class stations also have a "solar" clock as the sunlight data is sent at 60 second intervals.)
These measurements are used to avoid accessing the station's USB port at the same time as it is receiving data or logging data, as this is known to cause some stations' USB ports to become inaccessible.
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

   2018-05-28 21:03:02:pywws.service.underground:HTTPSConnectionPool(host='rtupdate.wunderground.com', port=443): Max retries exceeded with url: /weatherstation/updateweatherstation.php?rtfreq=48&winddir=5&softwaretype=pywws&windspeedmph=0.67&tempf=68.7&dateutc=2018-05-28+20%3A02%3A35&dewptf=65.3&action=updateraw&ID=ISURREYE4&windgustmph=2.24&PASSWORD=xxxxxxxx&baromin=30.0910&humidity=89&realtime=1&dailyrainin=0.122173&rainin=0 (Caused by NewConnectionError('<requests.packages.urllib3.connection.VerifiedHTTPSConnection object at 0xb25a3f30>: Failed to establish a new connection: [Errno -2] Name or service not known',))
   2018-05-28 21:03:15:pywws.service.openweathermap:HTTPConnectionPool(host='api.openweathermap.org', port=80): Max retries exceeded with url: /data/3.0/measurements?appid=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (Caused by NewConnectionError('<requests.packages.urllib3.connection.HTTPConnection object at 0xb25a3db0>: Failed to establish a new connection: [Errno 101] Network is unreachable',))

   2018-05-29 20:38:42:pywws.service.underground:http status: 500
   2018-05-29 20:39:23:pywws.service.underground:server response "success"
   
   2018-05-30 18:19:59:pywws.service.wetterarchivde:http status: 504
   2018-05-30 18:20:39:pywws.service.wetterarchivde:server response "{'info': 'Report exists at 2018-05-30T17:19:00.000Z', 'version': '6.0', 'status': 'SUCCESS', 'log': 'dbea2445-d930-4053-89ea-20c04a5030c1'}"
   2018-05-30 18:24:17:pywws.service.wetterarchivde:server response "{'version': '6.0', 'status': 'SUCCESS'}"
   
   2018-05-31 01:50:04:pywws.service.openweathermap:('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))
   2018-05-31 01:50:44:pywws.service.openweathermap:OK

To avoid swamping the log files duplicate messages are not logged.
When the response changes it is logged again.

Status
------

.. code-block:: none

   2015-09-01 21:50:21:pywws.weather_station:status {'lost_connection': True, 'rain_overflow': False}

The raw weather station data includes some "status" bits.
If any of these bits changes value when pywws is running, the status value is logged.
The most common problem is ``lost_connection``: the weather station console is not receiving data from the outside sensors.
Contact is often restored a few minutes later, but if not you may need to reset your weather station console by taking its batteries out.
The ``rain_overflow`` bit is set when the rain gauge counter has reached its maximum value and gone back to zero.

There are 6 bits of data in the status byte whose function is not yet known.
If any of these bits is set the value will be added to the reported status.
Do let me know if this happens as it might enable us to find the meaning of the unused bits.

Log extended
------------

.. code-block:: none

   2018-05-29 22:16:19:pywws.weatherstation:live_data log extended
   2018-05-29 22:32:19:pywws.weatherstation:live_data log extended
   2018-05-29 22:48:19:pywws.weatherstation:live_data log extended
   2018-05-29 23:04:19:pywws.weatherstation:live_data log extended

This shows a curiosity in the weather station's internal processing.
As the internal and external sensors drift there comes a time when an external reading is expected at the same time as the station is due to log some data.
To avoid a clash the station delays logging by one minute.
As the external readings are at 48 second intervals this avoids the problem until 16 minutes later (with the normal 5 minute logging interval) when another one minute delay is needed.
Eventually the clocks drift apart and normal operation is resumed.

The ``3080`` class stations also receive solar data at 60 second intervals.
If this clashes with the logging time the station delays logging by one minute.
Unfortunately this doesn't help, so the station effectively stops logging data until the clocks drift apart again.
If you are running pywws "live logging" then it will cover the gap by saving live readings at five minute intervals (if your logging interval is set to five minutes) until the station resumes normal operation.
If you are running "hourly" logging then you may get a large gap in your data.

Rain reset
----------

.. code-block:: none

   2015-08-25 13:30:51:pywws.process:2015-08-25 12:30:48 rain reset 1048.4 -> 1047.1
   2015-08-25 13:35:51:pywws.process:2015-08-25 12:30:48 rain reset 1048.4 -> 1047.1
   2015-08-25 13:40:51:pywws.process:2015-08-25 12:30:48 rain reset 1048.4 -> 1047.1

The raw rainfall data from the outside sensors is the total number of times the "see saw" has tipped since the external sensors were last reset (by a battery change, unless you do it quickly).
This number should only ever increase, so the :py:mod:`pywws.process` module warns of any decrease in the value as it may indicate corrupted data that needs manually correcting.
The logging message includes the UTC time stamp of the problem data to help you find it.

Live data missed
----------------

.. code-block:: none

   2015-10-30 04:49:56:pywws.weatherstation:live_data missed

Sometimes pywws fails to capture live data.
This happens if a new data record is identical to the previous one so pywws doesn't detect a change.
This is unlikely to happen if you are receiving wind data properly.

Note that this is just an occasional missing "live" record though, so if it does not happen often you shouldn't worry too much about it.

"Live log" synchronisation
--------------------------

If you run pywws at a high verbosity you may see messages like the following:

.. code-block:: none

   jim@gordon:~ $ pywws-livelog -vv ~/weather/data/
   10:32:46:pywws.logger:pywws version 18.5.0, build 1541 (d505b50)
   10:32:46:pywws.logger:Python version 3.5.3 (default, Jan 19 2017, 14:11:04) [GCC 6.3.0 20170124]
   10:32:46:pywws.weatherstation:using pywws.device_libusb1
   10:32:48:pywws.calib:Using user calibration
   10:32:51:pywws.weatherstation:read period 5
   10:32:51:pywws.weatherstation:delay 3, pause 0.5
   10:32:52:pywws.weatherstation:status {'rain_overflow': False, 'lost_connection': False}
   10:32:52:pywws.weatherstation:delay 3, pause 0.5
   10:32:53:pywws.weatherstation:delay 3, pause 0.5
   10:32:54:pywws.weatherstation:delay 3, pause 0.5
   10:32:54:pywws.weatherstation:delay 3, pause 0.5
   10:32:55:pywws.weatherstation:delay 3, pause 0.5
   10:32:56:pywws.weatherstation:delay 3, pause 0.5
   10:32:56:pywws.weatherstation:delay 3, pause 0.5
   10:32:57:pywws.weatherstation:delay 3, pause 0.5
   10:32:58:pywws.weatherstation:delay 3, pause 0.5
   10:32:58:pywws.weatherstation:delay 3, pause 0.5
   10:32:59:pywws.weatherstation:delay 3, pause 0.5
   10:33:00:pywws.weatherstation:delay 3, pause 0.5
   10:33:00:pywws.weatherstation:delay 3, pause 0.5
   10:33:01:pywws.weatherstation:delay 3, pause 0.5
   10:33:02:pywws.weatherstation:delay 3, pause 0.5
   10:33:02:pywws.weatherstation:live_data new data
   10:33:02:pywws.weatherstation:setting sensor clock 14.7283
   10:33:02:pywws.regulartasks:doing task sections ['live']
   10:33:03:pywws.service.underground:thread started Thread-2
   10:33:03:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): rtupdate.wunderground.com
   10:33:03:pywws.service.openweathermap:thread started Thread-4
   10:33:03:pywws.weatherstation:delay 3, pause 43.4936
   10:33:03:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): api.openweathermap.org
   10:33:03:requests.packages.urllib3.connectionpool:http://api.openweathermap.org:80 "POST /data/3.0/measurements?appid=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx HTTP/1.1" 204 0
   10:33:03:pywws.service.openweathermap:OK
   10:33:03:pywws.service.openweathermap:1 record sent
   10:33:04:requests.packages.urllib3.connectionpool:https://rtupdate.wunderground.com:443 "GET /weatherstation/updateweatherstation.php?baromin=29.9877&dewptf=63.2&ID=ISURREYE4&action=updateraw&dailyrainin=0&windgustmph=3.13&softwaretype=pywws&winddir=48&tempf=68.5&dateutc=2018-05-31+09%3A33%3A02&realtime=1&windspeedmph=1.57&humidity=83&rtfreq=48&PASSWORD=xxxxxxxxxxxx&rainin=0 HTTP/1.1" 200 8
   10:33:04:pywws.service.underground:server response "success"
   10:33:04:pywws.service.underground:1 record sent
   10:33:47:pywws.weatherstation:delay 3, pause 0.5
   10:33:47:pywws.weatherstation:avoid 5.795123949846001
   10:33:53:pywws.weatherstation:live_data new data
   10:33:53:pywws.regulartasks:doing task sections ['live']
   10:33:54:pywws.weatherstation:delay 4, pause 15.0615
   10:33:56:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): api.openweathermap.org
   10:33:56:requests.packages.urllib3.connectionpool:http://api.openweathermap.org:80 "POST /data/3.0/measurements?appid=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx HTTP/1.1" 204 0
   10:33:56:pywws.service.openweathermap:OK
   10:33:56:pywws.service.openweathermap:1 record sent
   10:33:56:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): rtupdate.wunderground.com
   10:33:57:requests.packages.urllib3.connectionpool:https://rtupdate.wunderground.com:443 "GET /weatherstation/updateweatherstation.php?baromin=29.9877&dewptf=63.2&ID=ISURREYE4&action=updateraw&dailyrainin=0&windgustmph=2.24&softwaretype=pywws&winddir=38&tempf=68.5&dateutc=2018-05-31+09%3A33%3A50&realtime=1&windspeedmph=0.67&humidity=83&rtfreq=48&PASSWORD=xxxxxxxxxxxx&rainin=0 HTTP/1.1" 200 8
   10:33:57:pywws.service.underground:server response "success"
   10:33:57:pywws.service.underground:1 record sent
   10:34:09:pywws.weatherstation:delay 4, pause 0.5
   10:34:10:pywws.weatherstation:avoid 5.808650196657673
   10:34:16:pywws.weatherstation:live_data new ptr: 005470
   10:34:16:pywws.process:Generating summary data
   10:34:16:pywws.process:daily: 2018-05-31 09:00:00
   10:34:16:pywws.process:monthly: 2018-05-01 09:00:00
   10:34:16:pywws.regulartasks:doing task sections ['logged']
   10:34:16:pywws.service.cwop:thread started Thread-1
   10:34:17:pywws.service.wetterarchivde:thread started Thread-3
   10:34:17:pywws.service.metoffice:thread started Thread-5
   10:34:17:pywws.weatherstation:delay 0, pause 18.132
   10:34:17:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): interface.wetterarchiv.de
   10:34:17:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): wow.metoffice.gov.uk
   10:34:17:requests.packages.urllib3.connectionpool:http://interface.wetterarchiv.de:80 "POST /weather/ HTTP/1.1" 200 36
   10:34:17:pywws.service.wetterarchivde:server response "{'status': 'SUCCESS', 'version': '6.0'}"
   10:34:17:pywws.service.wetterarchivde:1 record sent
   10:34:17:pywws.service.cwop:server software: b'# javAPRSSrvr 4.3.0b17'
   10:34:17:pywws.service.cwop:login: "user EW4610 pass -1 vers pywws 18.5.0"
   10:34:17:pywws.service.cwop:packet: "EW4610>APRS,TCPIP*:@310934z5121.90N/00015.07W_038/001g002t069r000p000b10155h83.pywws-18.5.0"
   10:34:17:pywws.service.cwop:server login ack: b'# logresp EW4610 unverified, server CWOP-2'
   10:34:17:pywws.service.cwop:OK
   10:34:17:pywws.service.cwop:1 record sent
   10:34:17:requests.packages.urllib3.connectionpool:http://wow.metoffice.gov.uk:80 "GET /automaticreading?baromin=29.9877&dewptf=63.2&softwaretype=pywws-18.5.0&dailyrainin=0.0000&windgustmph=2.24&siteid=18837259&winddir=38&tempf=68.5&dateutc=2018-05-31+09%3A34%3A13&windspeedmph=0.67&humidity=83&siteAuthenticationKey=xxxxxx&rainin=0.0000 HTTP/1.1" 200 2
   10:34:17:pywws.service.metoffice:OK
   10:34:17:pywws.service.metoffice:1 record sent
   ^C10:34:21:pywws.storage:waiting for thread Thread-2
   10:34:21:pywws.storage:waiting for thread Thread-4
   10:34:21:pywws.storage:waiting for thread Thread-3
   10:34:21:pywws.storage:waiting for thread Thread-1
   10:34:21:pywws.storage:waiting for thread Thread-5
   10:34:21:pywws.storage:flushing

The "read period" message at 10:32:51 shows that the weather station has the usual 5 minute logging interval.
The "delay 3, pause 0.5" messages show pywws waiting for the station to receive data from the outside sensors.
The ``delay`` value is the number of minutes since the station last logged some data.
The ``pause`` value is how many seconds pywws will wait before fetching data from the station again.
At 10:33:02 new data is received and the "sensor" clock is set.
After initiating uploads to ``underground`` and ``openweathermap`` the live logging loop sleeps for 43 seconds.
The uploads happen in their own threads while the main loop is paused.
At 10:33:47 the main loop resumes polling the station.
Almost immediately it pauses for 5.8 seconds to avoid USB activity around the time the station should receive external data.
At 10:34:10 USB activity is avoided when the station is expected to "log" data.
At 10:34:16 the new memory pointer is detected and the logged data is processed.
At 10:34:21 I pressed ``Ctrl-C`` to terminate the program.
After shutting down the upload threads any unsaved data is flushed to file and the program finishes.

Crash with traceback
--------------------

Sometimes pywws software crashes.
When it does, the log file will often contain a traceback like this:

.. code-block:: none
   :linenos:
   
   2018-05-31 11:13:47:pywws.livelog:LIBUSB_ERROR_IO [-1]
   Traceback (most recent call last):
     File "/usr/local/lib/python3.5/dist-packages/pywws-18.5.0-py3.5.egg/pywws/livelog.py", line 70, in live_log
       logged_only=(not tasks.has_live_tasks())):
     File "/usr/local/lib/python3.5/dist-packages/pywws-18.5.0-py3.5.egg/pywws/logdata.py", line 245, in live_data
       for data, ptr, logged in self.ws.live_data(logged_only=logged_only):
     File "/usr/local/lib/python3.5/dist-packages/pywws-18.5.0-py3.5.egg/pywws/weatherstation.py", line 546, in live_data
       new_ptr = self.current_pos()
     File "/usr/local/lib/python3.5/dist-packages/pywws-18.5.0-py3.5.egg/pywws/weatherstation.py", line 704, in current_pos
       self._read_fixed_block(0x0020), self.lo_fix_format['current_pos'])
     File "/usr/local/lib/python3.5/dist-packages/pywws-18.5.0-py3.5.egg/pywws/weatherstation.py", line 760, in _read_fixed_block
       result += self._read_block(mempos)
     File "/usr/local/lib/python3.5/dist-packages/pywws-18.5.0-py3.5.egg/pywws/weatherstation.py", line 748, in _read_block
       new_block = self.cusb.read_block(ptr)
     File "/usr/local/lib/python3.5/dist-packages/pywws-18.5.0-py3.5.egg/pywws/weatherstation.py", line 342, in read_block
       if not self.dev.write_data(buf):
     File "/usr/local/lib/python3.5/dist-packages/pywws-18.5.0-py3.5.egg/pywws/device_libusb1.py", line 131, in write_data
       0x200, 0, str_buf, timeout=50)
     File "/usr/lib/python3/dist-packages/usb1/__init__.py", line 1390, in controlWrite
       sizeof(data), timeout)
     File "/usr/lib/python3/dist-packages/usb1/__init__.py", line 1366, in _controlTransfer
       mayRaiseUSBError(result)
     File "/usr/lib/python3/dist-packages/usb1/__init__.py", line 133, in mayRaiseUSBError
       __raiseUSBError(value)
     File "/usr/lib/python3/dist-packages/usb1/__init__.py", line 125, in raiseUSBError
       raise __STATUS_TO_EXCEPTION_DICT.get(value, __USBError)(value)
   usb1.USBErrorIO: LIBUSB_ERROR_IO [-1]


Line 1 shows the exception that caused the crash.
Lines 3 to 26 show where in the program the problem happened.
Usually the last one is of interest, but the other function calls show how we got there.
Line 27 shows the full exception.
In this case it's a USBError raised by the libusb1 library.
