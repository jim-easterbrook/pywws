.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-14  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

How to set up 'live' logging with pywws
=======================================

Introduction
------------

There are two quite different modes of operation with pywws.
Traditionally :py:mod:`pywws.Hourly` would be run at regular intervals (usually an hour) from cron.
This is suitable for fairly static websites, but more frequent updates can be useful for sites such as Weather Underground (http://www.wunderground.com/).
The newer :py:mod:`pywws.LiveLog` program runs continuously and can upload data every 48 seconds.

Getting started
---------------

First of all, you need to install pywws and make sure it can get data from your weather station.
See :doc:`getstarted` for details.

If you have previously been using :py:mod:`pywws.Hourly` then disable your 'cron' job (or whatever else you use to run it) so it no longer runs.
You should not run :py:mod:`pywws.Hourly` and :py:mod:`pywws.LiveLog` at the same time.

Try running :py:mod:`pywws.LiveLog` from the command line, with a high level of verbosity so you can see what's happening.
Use the ``pywws-livelog`` command to run :py:mod:`pywws.LiveLog`::

   pywws-livelog -vvv ~/weather/data

Within five minutes (assuming you have set a 5 minute logging interval) you should see a 'live_data new ptr' message, followed by fetching any new data from the weather station and processing it.
Let :py:mod:`pywws.LiveLog` run for a minute or two longer, then kill the process by typing '<Ctrl>C'.

.. versionchanged:: 14.04.dev1194
   the ``pywws-livelog`` command replaced ``scripts/pywws-livelog.py``.

Configuring file locations
--------------------------

Open your weather.ini file with a text editor.
You should have a ``[paths]`` section similar to the following (where ``xxx`` is your user name)::

  [paths]
  work = /tmp/weather
  templates = /home/xxx/weather/templates/
  graph_templates = /home/xxx/weather/graph_templates/
  local_files = /home/xxx/weather/results/

Edit these to suit your installation and preferences.
``work`` is an existing temporary directory used to store intermediate files, ``templates`` is the directory where you keep your text template files, ``graph_templates`` is the directory where you keep your graph template files and ``local_files`` is a directory where template output that is not uploaded to your web site is put.
Don't use the pywws example directories for your templates, as they will get over-written when you upgrade pywws.

Copy your text and graph templates to the appropriate directories.
You may find some of the examples provided with pywws useful to get started.
The ``pywws-version -v`` command should show you where the examples are on your computer.

.. versionadded:: 14.04.dev1194
   the ``pywws-version`` command.

Configuring periodic tasks
--------------------------

In weather.ini you should have a ``[live]`` section similar to the following::

   [live]
   services = []
   plot = []
   text = []

This section specifies what pywws should do every time it gets a new reading from the weather station, i.e. every 48 seconds.
The ``services`` entry is a list of online weather services to upload data to, e.g. ``['underground_rf']``.
The ``plot`` and ``text`` entries are lists of template files for plots and text files to be processed and, optionally, uploaded to your web site.
You should probably leave all of these blank except for ``services``.

If you use YoWindow (http://yowindow.com/) you can add an entry to the ``[live]`` section to specify your YoWindow file, e.g.::

   [live]
   services = ['underground_rf']
   text = [('yowindow.xml', 'L')]
   ...

Note the use of the ``'L'`` flag -- this tells pywws to copy the template result to your "local files" directory instead of uploading it to your ftp site.

If you don't already have them, create four more sections in your weather.ini file: ``[logged]``, ``[hourly]``, ``[12 hourly]`` and ``[daily]``.
These sections should have similar entries to the ``[live]`` section, and specify what to do every time data is logged (5 to 30 minutes, depending on your logging interval), every hour, twice daily and once per day.
Add the names of your template files to the appropriate entries, for example::

   [logged]
   services = ['underground', 'metoffice']
   plot = []
   text = []

   [hourly]
   services = []
   plot = ['7days.png.xml', '24hrs.png.xml', 'rose_24hrs.png.xml']
   text = [('tweet.txt', 'T'), '24hrs.txt', '6hrs.txt', '7days.txt']

   [12 hourly]
   services = []
   plot = []
   text = []

   [daily]
   services = []
   plot = ['28days.png.xml']
   text = [('forecast.txt', 'T'), 'allmonths.txt']

Note the use of the ``'T'`` flag -- this tells pywws to send the template result to Twitter instead of uploading it to your ftp site.

.. versionadded:: 14.05.dev1211
   ``[cron name]`` sections.
   If you need more flexibility in when tasks are done you can use ``[cron name]`` sections.
   See :doc:`weather_ini` for more detail.

.. versionchanged:: 13.06_r1015
   added the ``'T'`` flag.
   Previously Twitter templates were listed separately in ``twitter`` entries in the ``[hourly]`` and other sections.
   The older syntax still works, but is deprecated.

.. versionchanged:: 13.05_r1013
   added a ``'yowindow.xml'`` template.
   Previously yowindow files were generated by a separate module, invoked by a ``yowindow`` entry in the ``[live]`` section.
   This older syntax still works, but is deprecated.

Asynchronous uploads
--------------------

.. versionadded:: 13.09_r1057

Uploading data to web sites or 'services' can sometimes take a long time, particularly if a site has gone off line and the upload times out.
In normal operation pywws waits until all uploads have been processed before fetching any more data from the weather station.
This can lead to data sometimes being missed.

The ``asynchronous`` item in the ``[config]`` section of weather.ini can be set to ``True`` to tell :py:mod:`pywws.LiveLog` to do these uploads in a separate thread.

Run in the background
---------------------

.. versionadded:: 13.12.dev1118

In order to have :py:mod:`pywws.LiveLog` carry on running after you finish using your computer it needs to be run as a "background job".
On most Linux / UNIX systems you can do this by putting an ampersand ('&') at the end of the command line.
Running a job in the background like this doesn't always work as expected: the job may suspend when you log out.
It's much better to run as a proper UNIX 'daemon' process.

The :py:mod:`pywws.livelogdaemon` program does this, if you have the `python-daemon <https://pypi.python.org/pypi/python-daemon/>`_ library installed::

   pywws-livelog-daemon -v ~/weather/data ~/weather/data/pywws.log start

Note that the log file is a required parameter, not an option.

Automatic restarting
--------------------

There are various ways of configuring a Linux system to start a program when the machine boots up.
Typically these involve putting a file in ``/etc/init.d/``, which requires root privileges.
A slightly harder problem is ensuring a program restarts if it crashes.
My solution to both problems is to run the following script from cron, several times an hour. ::

   #!/bin/sh

   export PATH=$PATH:/usr/local/bin

   # exit if NTP hasn't set computer clock
   [ `ntpdc -c sysinfo | awk '/stratum:/ {print $2}'` -ge 10 ] && exit

   pidfile=/var/run/pywws.pid
   datadir=/home/jim/weather/data
   logfile=$datadir/live_logger.log

   # exit if process is running
   [ -f $pidfile ] && kill -0 `cat $pidfile` && exit

   # email last few lines of the logfile to see why it died
   if [ -f $logfile ]; then
     log=/tmp/log-weather
     tail -40 $logfile >$log
     /home/jim/scripts/email-log.sh $log "weather log"
     rm $log
     fi

   # restart process
   pywws-livelog-daemon -v -p $pidfile $datadir $logfile start

The process id of the daemon is stored in ``pidfile``.
If the process is running, the script does nothing.
If the process has crashed, it emails the last 40 lines of the log file to me (using a script that creates a message and passes it to sendmail) and then restarts :py:mod:`pywws.livelogdaemon`.
You'll need to edit this quite a lot to suit your file locations and so on, but it gives some idea of what to do.