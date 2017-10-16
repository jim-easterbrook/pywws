.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-15  pywws contributors

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

weather.ini - configuration file format
=======================================

Nearly all configuration of pywws is via a single file in the data
directory: weather.ini. This file has a structure similar to that of
Microsoft Windows INI files. It is divided into "sections", each of which
has a number of "name = value" entries. The order in which sections appear
is not important.

Any plain text editor can be used to do edit the file.
(Don't try to edit it while any other pywws software is running.)
In many cases pywws will initialise the entries to sensible values.

Another file, status.ini, is used to store some information that pywws uses internally.
It is described at the end of this document.
In normal use you should not need to edit it.

The following sections are currently in use:

  * config: miscellaneous system configuration.
  * paths: directories in which templates etc. are stored.
  * live: tasks to be done every 48 seconds.
  * logged: tasks to be done every time the station logs a data record.
  * cron: tasks to be done at a particular time or date.
  * hourly: tasks to be done every hour.
  * 12 hourly: tasks to be done every 12 hours.
  * daily: tasks to be done every day.
  * ftp: configuration of uploading to a website.
  * twitter: configuration of posting to Twitter.
  * underground, metoffice, temperaturnu etc: configuration of posting to 'services'.

.. _weather_ini-config:

config: miscellaneous system configuration
------------------------------------------
::

 [config]
 ws type = 1080
 day end hour = 21
 pressure offset = 9.4
 gnuplot encoding = iso_8859_1
 template encoding = iso-8859-1
 language = en
 logdata sync = 1
 rain day threshold = 0.2
 asynchronous = False
 usb activity margin = 3.0
 gnuplot version = 4.2
 frequent writes = False

``ws type`` is the "class" of weather station. It should be set to ``1080`` for most weather stations, or ``3080`` if your station console displays solar illuminance.
 
``day end hour`` is the end of the "`meteorological day <http://en.wikipedia.org/wiki/Meteorological_day>`_", in local time without daylight savings time. Typical values are 21, 9, or 24.
You must update all your stored data by running :py:mod:`pywws.Reprocess` after you change this value.

``pressure offset`` is the difference between absolute and relative (sea level) air pressure.
The initial value is copied from the weather station, assuming you have set it up to display the correct relative pressure, but you can adjust the value in weather.ini to calibrate your station.
You must update all your stored data by running :py:mod:`pywws.Reprocess` after you change this value.

.. versionchanged:: 13.10_r1082
   made ``pressure offset`` a config item.
   Previously it was always read from the weather station.

``gnuplot encoding`` is the text encoding used when plotting graphs. The default value of ``iso_8859_1`` allows the degree symbol, which is useful in a weather application! Other values might be needed if your language includes accented characters. The possible values depend on your gnuplot installation so some experimentation may be needed.

``template encoding`` is the text encoding used for templates.
The default value is ``iso-8859-1``, which is the encoding used in the example templates.
If you create templates with a different character set, you should change this value to match your templates.

``language`` is used to localise pywws. It's optional, as pywws usually uses the computer's default language as set by the LANG environment variable. The available languages are those in the ``translations`` subdirectory of your pywws installation. If you set any other language, pywws will fall back to using English.

``logdata sync`` sets the quality of synchronisation used by :doc:`../api/pywws.LogData`. Set it to 0 for fast & inaccurate or 1 for slower but precise.

``rain day threshold`` is the amount of rain (in mm) that has to fall in one day for it to qualify as a rainy day in the monthly summary data.
You must update all your stored data by running :py:mod:`pywws.Reprocess` after you change this value.

.. versionadded:: 13.09_r1057
   ``asynchrouous`` controls the use of a separate upload thread in :py:mod:`pywws.LiveLog`.

.. versionadded:: 13.10_r1094
   ``usb activity margin`` controls the algorithm that avoids the "USB lockup" problem that affects some stations.
   It sets the number of seconds either side of expected station activity (receiving a reading from outside or logging a reading) that pywws does not get data from the station.
   If your station is not affected by the USB lockup problem you can set ``usb activity margin`` to 0.0.

.. versionadded:: 13.11_r1102
   ``gnuplot version`` tells :py:mod:`pywws.Plot` and :py:mod:`pywws.WindRose` what version of gnuplot is installed on your computer.
   This allows them to use version-specific features to give improved plot quality.

.. versionadded:: 14.01_r1133
   ``frequent writes`` tells :py:mod:`pywws.Tasks` to save weather data and status to file every time there is new logged data.
   The default is to save the files every hour, to reduce "wear" on solid state memory such as the SD cards used with Raspberry Pi computers.
   If your weather data directory is stored on a conventional disc drive you can set ``frequent writes`` to ``True``.

paths: directories in which templates etc. are stored
-----------------------------------------------------
::

 [paths]
 templates = /home/$USER/weather/templates/
 graph_templates = /home/$USER/weather/graph_templates/
 user_calib = /home/$USER/weather/modules/usercalib
 work = /tmp/weather
 local_files = /home/$USER/weather/results/

These entries specify where your text templates and graph templates are stored, where temporary files should be created, where template output (that is not uploaded) should be put, and (if you have one) the location of your calibration module.

live: tasks to be done every 48 seconds
---------------------------------------
::

 [live]
 services = ['underground_rf']
 text = [('yowindow.xml', 'L')]
 plot = []

This section specifies tasks that are to be carried out for every data sample during 'live logging', i.e. every 48 seconds.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.
pywws will automatically limit the frequency of service uploads according to each service's specification.

``text`` and ``plot`` are lists of text and plot templates to be processed and, optionally, uploaded to your website.

.. versionchanged:: 13.05_r1013
   added a ``'yowindow.xml'`` template.
   Previously yowindow files were generated by a separate module, invoked by a ``yowindow`` entry in the ``[live]`` section.
   This older syntax still works, but is deprecated.

logged: tasks to be done every time the station logs a data record
------------------------------------------------------------------
::

 [logged]
 services = ['underground', 'metoffice']
 text = []
 plot = []

This section specifies tasks that are to be carried out every time a data record is logged when 'live logging' or every time an hourly cron job is run.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.

``text`` and ``plot`` are lists of text and plot templates to be processed and, optionally, uploaded to your website.

cron: tasks to be done at a particular time or date
---------------------------------------------------

.. versionadded:: 14.05.dev1211

::

 [cron prehourly]
 format = 59 * * * *
 plot = [('tweet.png.xml', 'L')]
 services = []
 text = []

 [cron hourly]
 format = 0 * * * *
 plot = ['7days.png.xml', '2014.png.xml', '24hrs.png.xml', 'rose_12hrs.png.xml']
 text = [('tweet.txt', 'T'), '24hrs.txt', '6hrs.txt', '7days.txt', '2014.txt']
 services = []

 [cron daily 9]
 format = 0 9 * * *
 plot = ['28days.png.xml']
 text = [('forecast.txt', 'T'), 'forecast_9am.txt', 'forecast_week.txt']
 services = []

 [cron daily 21]
 format = 0 21 * * *
 text = ['forecast_9am.txt']
 services = []
 plot = []

 [cron weekly]
 format = 0 9 * * 6
 plot = ['2008.png.xml', '2009.png.xml', '2010.png.xml', '2011.png.xml',
         '2012.png.xml', '2013.png.xml']
 text = ['2008.txt', '2009.txt', '2010.txt', '2011.txt', '2012.txt', '2013.txt']
 services = []

``[cron name]`` sections provide a very flexible way to specify tasks to be done at a particular time and/or date.
``name`` can be anything you like, but each ``[cron name]`` section must have a unique name.

To use ``[cron name]`` sections you need to install the "croniter" package.
See :doc:`../essentials/dependencies` for more detail.

``format`` specifies when the tasks should be done (in local time), in the usual crontab format.
(See ``man 5 crontab`` on any Linux computer.)
Processing is not done exactly on the minute, but when the next live or logged data arrives.

hourly: tasks to be done every hour
-----------------------------------
::

 [hourly]
 services = []
 text = [('tweet.txt', 'T'), '24hrs.txt', '6hrs.txt', '7days.txt', 'feed_hourly.xml']
 plot = ['7days.png.xml', '24hrs.png.xml', 'rose_12hrs.png.xml']

This section specifies tasks that are to be carried out every hour when 'live logging' or running an hourly cron job.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.

``text`` and ``plot`` are lists of text and plot templates to be processed and, optionally, uploaded to your website.

.. versionchanged:: 13.06_r1015
   added the ``'T'`` flag.
   Previously Twitter templates were listed separately in ``twitter`` entries in the ``[hourly]`` and other sections.
   The older syntax still works, but is deprecated.

12 hourly: tasks to be done every 12 hours
------------------------------------------
::

 [12 hourly]
 services = []
 text = []
 plot = []

This section specifies tasks that are to be carried out every 12 hours when 'live logging' or running an hourly cron job. Use it for things that don't change very often, such as monthly graphs.
The tasks are done at your day end hour, and 12 hours later.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.

``text`` and ``plot`` are lists of text and plot templates to be processed and, optionally, uploaded to your website.

daily: tasks to be done every 24 hours
--------------------------------------
::

 [daily]
 services = []
 text = ['feed_daily.xml']
 plot = ['2008.png.xml', '2009.png.xml', '2010.png.xml', '28days.png.xml']

This section specifies tasks that are to be carried out every day when 'live logging' or running an hourly cron job. Use it for things that don't change very often, such as monthly or yearly graphs.
The tasks are done at your day end hour.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.

``text`` and ``plot`` are lists of text and plot templates to be processed and, optionally, uploaded to your website.

ftp: configuration of uploading to a website
--------------------------------------------
::

 [ftp]
 local site = False
 secure = False
 site = ftp.your_isp.co.uk
 user = username
 password = userpassword
 directory = public_html/weather/data/
 port = 21

These entries provide details of your website (or local directory) where processed text files and graph images should be transferred to.

``local site`` specifies whether the files should be copied to a local directory or sent to a remote site. You may want to set this if you run your web server on the same machine as you are running pywws on.

``secure`` specifies whether to transfer files using SFTP (secure FTP) instead of the more common FTP. Your web site provider should be able to tell you if you can use SFTP.
Note that you may need to change the ``port`` value when you change to or from secure mode.

``site`` is the web address of the FTP site to transfer files to.

``user`` and ``password`` are the FTP site login details. Your web site provider should have provided them to you.

``privkey`` is the path to a private SSH-key_. For SFTP (secure FTP) this can be used for authentication instead of a password, which offers additional benefits in terms of security. When this is used the password-parameter can be left empty.

.. _SSH-key: https://www.ssh.com/ssh/public-key-authentication

``directory`` specifies where on the FTP site (or local file system) the files should be stored. Note that you may have to experiment with this a bit - you might need a '/' character at the start of the path.

.. versionadded:: 13.12.dev1120
   ``port`` specifies the port number to use.
   Default value is 21 for FTP, 22 for SFTP.
   Your web site provider may tell you to use a different port number.

twitter: configuration of posting to Twitter
--------------------------------------------
::

 [twitter]
 secret = longstringofrandomcharacters
 key = evenlongerstringofrandomcharacters
 latitude = 51.365
 longitude = -0.251

``secret`` and ``key`` are authentication data provided by Twitter. To set them, run :py:mod:`pywws.TwitterAuth`.

``latitude`` and ``longitude`` are optional location data. If you include them then your weather station tweets will have location information so users can see where your weather station is. It might also enable people to find your weather station tweets if they search by location.

underground, metoffice, temperaturnu etc: configuration of posting to 'services'
--------------------------------------------------------------------------------
::

 [underground]
 station = IXYZABA5
 password = secret

These sections contain information such as passwords and station IDs needed to upload data to weather services. The names of the data entries depend on the service. The example shown is for Weather Underground.

``station`` is the PWS ID allocated to your weather station by Weather Underground.

``password`` is your Weather Underground password.

status.ini - status file format
===============================

This file is written by pywws and should not (usually) be edited.
The following sections are currently in use:

  * fixed: values copied from the weather station's "fixed block".
  * clock: synchronisation information.
  * last update: date and time of most recent task completions.

fixed: values copied from the weather station's "fixed block"
-------------------------------------------------------------
::

 [fixed]
 fixed block = {...}

``fixed block`` is all the data stored in the first 256 bytes of the station's memory.
This includes maximum and minimum values, alarm threshold settings, display units and so on.

clock: synchronisation information
----------------------------------
::

 [clock]
 station = 1360322930.02
 sensor = 1360322743.69

These values record the measured times when the station's clock logged some data and when the outside sensors transmitted a new set of data.
They are used to try and prevent the USB interface crashing if the computer accesses the weather station at the same time as either of these events, a common problem with many EasyWeather compatible stations.
The times are measured every 24 hours to allow for drift in the clocks.

last update: date and time of most recent task completions
----------------------------------------------------------
::

 [last update]
 hourly = 2013-05-30 19:04:15
 logged = 2013-05-30 19:04:15
 daily = 2013-05-30 09:04:15
 openweathermap = 2013-05-30 18:59:15
 underground = 2013-05-30 18:58:34
 metoffice = 2013-05-30 18:59:15
 12 hourly = 2013-05-30 09:04:15

These record date & time of the last successful completion of various tasks.
They are used to allow unsuccessful tasks (e.g. network failure preventing uploads) to be retried after a few minutes.
