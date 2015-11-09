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

How to set up 'hourly' logging with pywws
=========================================

Introduction
------------

There are two quite different modes of operation with pywws.
Traditionally :py:mod:`pywws.Hourly` would be run at regular intervals (usually an hour) from cron.
This is suitable for fairly static websites, but more frequent updates can be useful for sites such as Weather Underground (http://www.wunderground.com/).
The newer :py:mod:`pywws.LiveLog` program runs continuously and can upload data every 48 seconds.

Note that although this document (and the program name) refers to 'hourly' logging, you can run  :py:mod:`pywws.Hourly` as often or as infrequently as you like, but don't try to run it more often than double your logging interval.
For example, if your logging interval is 10 minutes, don't run :py:mod:`pywws.Hourly` more often than every 20 minutes.

Getting started
---------------

First of all, you need to install pywws and make sure it can get data from your weather station.
See :doc:`getstarted` for details.

Try running :py:mod:`pywws.Hourly` from the command line, with a high level of verbosity so you can see what's happening.
Use the ``pywws-hourly`` command to run :py:mod:`pywws.Hourly`::

   pywws-hourly -vvv ~/weather/data

Within five minutes (assuming you have set a 5 minute logging interval) you should see a 'live_data new ptr' message, followed by fetching any new data from the weather station and processing it.

.. versionchanged:: 14.04.dev1194
   the ``pywws-hourly`` command replaced ``scripts/pywws-hourly.py``.

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

In weather.ini you should have ``[logged]``, ``[hourly]``, ``[12 hourly]`` and ``[daily]`` sections similar to the following::

   [logged]
   services = []
   plot = []
   text = []

   [hourly]
   ...

These specify what :py:mod:`pywws.Hourly` should do when it is run.
Tasks in the ``[logged]`` section are done every time there is new logged data, tasks in the ``[hourly]`` section are done every hour, tasks in the ``[12 hourly]`` section are done twice daily and tasks in the ``[daily]`` section are done once per day.

The ``services`` entry is a list of online weather services to upload data to.
The ``plot`` and ``text`` entries are lists of template files for plots and text files to be processed and, optionally, uploaded to your web site.
Add the names of your template files and weather services to the appropriate entries, for example::

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

You can test that all these are working by removing the ``[last update]`` section from status.ini, then running :py:mod:`pywws.Hourly` again::

   pywws-hourly -v ~/weather/data

.. versionadded:: 14.05.dev1211
   ``[cron name]`` sections.
   If you need more flexibility in when tasks are done you can use ``[cron name]`` sections.
   See :doc:`weather_ini` for more detail.

.. versionchanged:: 13.06_r1015
   added the ``'T'`` flag.
   Previously Twitter templates were listed separately in ``twitter`` entries in the ``[hourly]`` and other sections.
   The older syntax still works, but is deprecated.

.. versionchanged:: 13.05_r1009
   the last update information was previously stored in weather.ini, with ``last update`` entries in several sections.

Run as a cron job
-----------------

Most UNIX/Linux systems have a 'cron' daemon that can run programs at certain times, even if you are not logged in to the computer.
You edit a 'crontab' file to specify what to run and when to run  it.
For example, to run :py:mod:`pywws.Hourly` every hour, at zero minutes past the hour::

   0 * * * *       pywws-hourly /home/xxx/weather/data

This might work, but if it didn't you probably won't get any error messages to tell you what went wrong.
It's much better to run a script that runs :py:mod:`pywws.Hourly` and then emails you any output it produces.
Here's the script I use::

   #!/bin/sh
   #
   # weather station logger calling script

   export PATH=$PATH:/usr/local/bin

   if [ ! -d ~/weather/data/ ]; then
     exit
     fi

   log=/var/log/log-weather

   pywws-hourly -v ~/weather/data >$log 2>&1

   # mail the log file
   /home/jim/scripts/email-log.sh $log "weather log"

You’ll need to edit this quite a lot to suit your file locations and so on, but it gives some idea of what to do.