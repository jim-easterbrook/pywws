.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

Some entries in the file are set by pywws, while others need to be edited
by the user. Any plain text editor can be used to do this. (Don't try to
edit the file while any other pywws software is running.) In many cases
pywws will initialise the entries to sensible values.

The following sections are currently in use:

  * config: miscellaneous system configuration.
  * paths: directories in which templates etc. are stored.
  * fixed: values copied from the weather station's "fixed block".
  * live: tasks to be done every 48 seconds.
  * logged: tasks to be done every time the station logs a data record.
  * hourly: tasks to be done every hour.
  * 12 hourly: tasks to be done every 12 hours.
  * daily: tasks to be done every day.
  * ftp: configuration of uploading to a website.
  * twitter: configuration of posting to Twitter.
  * underground, metoffice, temperaturnu etc: configuration of posting to 'services'.

config: miscellaneous system configuration
------------------------------------------
::

 [config]
 ws type = 1080
 altitude = 13
 latitude = 51.506419
 longitude = -0.099843
 day end hour = 21
 gnuplot encoding = iso_8859_1
 template encoding = iso-8859-1
 language = en
 logdata sync = 1
 rain day threshold = 0.2

``ws type`` is the "class" of weather station. It should be set to ``1080`` for most weather stations, or ``3080`` if your station console displays solar illuminance.

``altitude`` altitude of weather station, in meters.

``latitude`` of weather station in decimal format.

``longitude`` of weather station in decimal format.

``day end hour`` is the end of the "`meteorological day <http://en.wikipedia.org/wiki/Meteorological_day>`_", in local time without daylight savings time. Typical values are 21, 9, or 24.

``gnuplot encoding`` is the text encoding used when plotting graphs. The default value of ``iso_8859_1`` allows the degree symbol, which is useful in a weather application! Other values might be needed if your language includes accented characters. The possible values depend on your gnuplot installation so some experimentation may be needed.

``template encoding`` is the text encoding used for templates.
The default value is ``iso-8859-1``, which is the encoding used in the example templates.
If you create templates with a different character set, you should change this value to match your templates.

``language`` is used to localise pywws. It's optional, as pywws usually uses the computer's default language as set by the LANG environment variable. The available languages are those in the ``translations`` subdirectory of your pywws installation. If you set any other language, pywws will fall back to using English.

``logdata sync`` sets the quality of synchronisation used by :doc:`../api/pywws.LogData`. Set it to 0 for fast & inaccurate or 1 for slower but precise.

``rain day threshold`` is the amount of rain (in mm) that has to fall in one day for it to qualify as a rainy day in the monthly summary data.

paths: directories in which templates etc. are stored
-----------------------------------------------------
::

 [paths]
 templates = /home/$USER/weather/templates/
 graph_templates = /home/$USER/weather/graph_templates/
 user_calib = /home/jim/weather/modules/usercalib
 work = /tmp/weather

These three entries specify where your text templates and graph templates are stored, where temporary files should be created, and (if you have one) the location of your calibration module.

fixed: values copied from the weather station's "fixed block"
-------------------------------------------------------------
::

 [fixed]
 station clock = 1360322930.02
 sensor clock = 1360322743.69
 pressure offset = 7.4
 fixed block = {...}

This section is written by pywws and should not be edited.

live: tasks to be done every 48 seconds
---------------------------------------
::

 [live]
 services = ['underground']
 twitter = []
 text = []
 plot = []
 yowindow = /home/jim/data/yowindow.xml

This section specifies tasks that are to be carried out for every data sample during 'live logging', i.e. every 48 seconds. It is unlikely that you'd want to do anything other than upload to Weather Underground or update your YoWindow file this often.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.

``twitter`` is a list of text templates to be processed and posted to Twitter.

``text`` and ``plot`` are lists of text and plot templates to be processed and uploaded to your website.

``yowindow`` is the full path of an xml file to be generated for a YoWindow weather widget (see http://yowindow.com/). If you don't use YoWindow, leave this entry out.

logged: tasks to be done every time the station logs a data record
------------------------------------------------------------------
::

 [logged]
 services = ['underground', 'metoffice']
 twitter = ['tweet.txt']
 text = []
 plot = []

This section specifies tasks that are to be carried out every time a data record is logged when 'live logging' or every time an hourly cron job is run.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.

``twitter`` is a list of text templates to be processed and posted to Twitter.

``text`` and ``plot`` are lists of text and plot templates to be processed and uploaded to your website.

hourly: tasks to be done every hour
-----------------------------------
::

 [hourly]
 services = []
 twitter = ['tweet.txt']
 text = ['24hrs.txt', '6hrs.txt', '7days.txt', 'feed_hourly.xml', 'allmonths.txt']
 plot = ['7days.png.xml', '24hrs.png.xml', 'rose_12hrs.png.xml']

This section specifies tasks that are to be carried out every hour when 'live logging' or running an hourly cron job.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.

``twitter`` is a list of text templates to be processed and posted to Twitter.

``text`` and ``plot`` are lists of text and plot templates to be processed and uploaded to your website.

12 hourly: tasks to be done every 12 hours
------------------------------------------
::

 [12 hourly]
 services = []
 twitter = []
 text = []
 plot = []

This section specifies tasks that are to be carried out every 12 hours when 'live logging' or running an hourly cron job. Use it for things that don't change very often, such as monthly graphs.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.

``twitter`` is a list of text templates to be processed and posted to Twitter.

``text`` and ``plot`` are lists of text and plot templates to be processed and uploaded to your website.

daily: tasks to be done every 24 hours
--------------------------------------
::

 [daily]
 services = []
 twitter = []
 text = ['feed_daily.xml']
 plot = ['2008.png.xml', '2009.png.xml', '2010.png.xml', '28days.png.xml']

This section specifies tasks that are to be carried out every day when 'live logging' or running an hourly cron job. Use it for things that don't change very often, such as monthly or yearly graphs.

``services`` is a list of 'services' to upload data to. Each one listed must have a configuration file in ``pywws/services/``. See :doc:`../api/pywws.toservice` for more detail.

``twitter`` is a list of text templates to be processed and posted to Twitter.

``text`` and ``plot`` are lists of text and plot templates to be processed and uploaded to your website.

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

These entries provide details of your website (or local directory) where processed text files and graph images should be transferred to.

``local site`` specifies whether the files should be copied to a local directory or sent to a remote site. You may want to set this if you run your web server on the same machine as you are running pywws on.

``secure`` specifies whether to transfer files using SFTP (secure FTP) instead of the more common FTP. Your web site provider should be able to tell you if you can use SFTP.

``site`` is the web address of the FTP site to transfer files to.

``user`` and ``password`` are the FTP site login details. Your web site provider should have provided them to you.

``directory`` specifies where on the FTP site (or local file system) the files should be stored. Note that you may have to experiment with this a bit - you might need a '/' character at the start of the address.

twitter: configuration of posting to Twitter
--------------------------------------------
::

 [twitter]
 secret = longstringofrandomcharacters
 key = evenlongerstringofrandomcharacters
 latitude = 51.365
 longitude = -0.251

``secret`` and ``key`` are authentication data provided by Twitter. To set them, run the ``TwitterAuth.py`` program.

``latitude`` and ``longitude`` are optional location data. If you include them then your weather station tweets will have location information so users can see where your weather station is. It might also enable people to find your weather station tweets if they search by location.

underground, metoffice, temperaturnu etc: configuration of posting to 'services'
--------------------------------------------------------------------------------
::

 [underground]
 station = IXYZABA5
 password = secret
 last update = 2010-09-27 19:45:24

These sections contain information such as passwords and station IDs needed to upload data to weather services. The names of the data entries depend on the service. The example shown is for Weather Underground.

``station`` is the PWS ID allocated to your weather station by Weather Underground.

``password`` is your Weather Underground password.

``last update`` is set by pywws when you upload to a weather service.
