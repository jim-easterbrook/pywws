.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-18  pywws contributors

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
Traditionally :py:mod:`pywws.hourly` would be run at regular intervals (usually an hour) from cron.
This is suitable for fairly static websites, but more frequent updates can be useful for sites such as Weather Underground (http://www.wunderground.com/).
The newer :py:mod:`pywws.livelog` program runs continuously and can upload data every 48 seconds.

Getting started
---------------

First of all, you need to install pywws and make sure it can get data from your weather station.
See :doc:`getstarted` for details.

If you have previously been using :py:mod:`pywws.hourly` then disable your 'cron' job (or whatever else you use to run it) so it no longer runs.
You should never run :py:mod:`pywws.hourly` and :py:mod:`pywws.livelog` at the same time.

Try running :py:mod:`pywws.livelog` from the command line, with a high level of verbosity so you can see what's happening.
Use the ``pywws-livelog`` command to run :py:mod:`pywws.livelog`::

   pywws-livelog -vvv ~/weather/data

Within five minutes (assuming you have set a 5 minute logging interval) you should see a 'live_data new ptr' message, followed by fetching any new data from the weather station and processing it.
Let :py:mod:`pywws.livelog` run for a minute or two longer, then kill the process by typing '<Ctrl>C'.

.. versionchanged:: 14.04.dev1194
   the ``pywws-livelog`` command replaced ``scripts/pywws-livelog.py``.

Configuring file locations
--------------------------

Open your weather.ini file with a text editor.
You should have a ``[paths]`` section similar to the following (where ``xxx`` is your user name)::

  [paths]
  work = /tmp/pywws
  templates = /home/xxx/weather/templates/
  graph_templates = /home/xxx/weather/graph_templates/
  modules = /home/xxx/weather/modules/

Edit these to suit your installation and preferences.
``work`` is a temporary directory used to store intermediate files.
If your computer uses solid state storage, such as a Raspberry Pi's SD card, it's a good idea to make this a "RAM disk" to reduce storage "wear".
``templates`` is the directory where you keep your text template files, ``graph_templates`` is the directory where you keep your graph template files, and ``modules`` is a directory for any extra modules you write.
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
   text = []
   plot = []

This section specifies what pywws should do every time it gets a new reading from the weather station, i.e. every 48 seconds.
The ``services`` entry is a list of online weather services to upload data to, e.g. ``'underground'`` or ``('ftp', '24hrs.txt')``.
The ``plot`` and ``text`` entries are lists of template files for plots and text files to be processed.
You should probably leave all of these blank except for ``services``.

If you use YoWindow (http://yowindow.com/) you can add an entry to the ``[live]`` section to specify your YoWindow file, e.g.::

   [live]
   services = ['underground']
   text = ['yowindow.xml']
   plot = []

If you don't already have them, create four more sections in your weather.ini file: ``[logged]``, ``[hourly]``, ``[12 hourly]`` and ``[daily]``.
These sections should have similar entries to the ``[live]`` section, and specify what to do every time data is logged (5 to 30 minutes, depending on your logging interval), every hour, twice daily and once per day.
Add the names of your template files to the appropriate entries, for example::

   [logged]
   services = ['underground', 'metoffice']
   plot = []
   text = []

   [hourly]
   services = [('twitter', 'tweet.txt'),
               ('ftp', '7days.png', '24hrs.png', 'rose_24hrs.png',
                       '24hrs.txt', '6hrs.txt', '7days.txt')]
   plot = ['7days.png.xml', '24hrs.png.xml', 'rose_24hrs.png.xml']
   text = ['tweet.txt', '24hrs.txt', '6hrs.txt', '7days.txt']

   [12 hourly]
   services = []
   plot = []
   text = []

   [daily]
   services = [('twitter', 'forecast.txt'), ('ftp', '28days.png', 'allmonths.txt')]
   plot = ['28days.png.xml']
   text = ['forecast.txt', 'allmonths.txt']

Note that the ``twitter`` and ``ftp`` "services" use files generated by the ``plot`` and ``text`` items.
It's probably best not to add all of these at once.
You could start by uploading one file to your web site, then when that's working add the remaining web site files.
You can add Twitter and other services later on.

.. versionadded:: 14.05.dev1211
   ``[cron name]`` sections.
   If you need more flexibility in when tasks are done you can use ``[cron name]`` sections.
   See :doc:`weather_ini` for more detail.

Create a dedicated user (optional)
----------------------------------

As pywws will be running continuously, and contacting various computers on the internet, there is a very remote risk that one of its dependencies has a security flaw that might allow someone to gain unauthorised to your computer.
Running pywws as a user with minimal privileges adds a little extra protection.

You can create a user with the ``adduser`` command::

   sudo adduser --system --disabled-login --shell=/bin/false pywws

The exact syntax may vary according to your operating system.
The important thing is to create a user that can't login, and can't run ``sudo``, but does have a home directory.

Run in the background
---------------------

In order to have :py:mod:`pywws.livelog` carry on running after you finish using your computer it needs to be run as a "background job".
On most Linux / UNIX systems you can do this by putting an ampersand ('&') at the end of the command line.
Running a job in the background like this doesn't always work as expected: the job may suspend when you log out.
It's much better to run as a proper UNIX 'daemon' process.

Using systemd
^^^^^^^^^^^^^

On recent versions of Linux the systemd_ service manager makes it easy to create a daemon process.
The service is defined in a file ``/etc/systemd/system/pywws.service``::

   [Unit]
   Description=pywws weather station live logging
   After=time-sync.target

   [Service]
   Type=simple
   User=pywws
   Restart=on-failure
   ExecStart=/usr/local/bin/pywws-livelog -v -l systemd /home/pywws/data/

The ``[Unit]`` section says pywws shouldn't start until the computer has set its clock correctly. This is important on computers without a battery-backed real time clock, such as the Raspberry Pi.
The ``[Service]`` section specifies which user should run pywws and gives the command to run it.
The ``-l systemd`` option sends log messages to ``systemd`` instead of using a normal pywws log file.
You can use ``sudo service pywws start`` to test the ``pywws.service`` file.
After starting ``sudo service pywws status`` shows if it's running OK, and the last few log messages::

   jim@gordon:~ $ sudo service pywws status
   ● pywws.service - pywws weather station live logging
      Loaded: loaded (/etc/systemd/system/pywws.service; static; vendor preset: enabled)
      Active: active (running) since Thu 2018-08-23 17:49:01 BST; 12min ago
    Main PID: 30946 (pywws-livelog)
      CGroup: /system.slice/pywws.service
              └─30946 /usr/bin/python3 /usr/local/bin/pywws-livelog -v -l systemd /home/pywws/data/

   Aug 23 17:49:44 gordon pywws-livelog[30946]: pywws.service.wetterarchivde:server response "{'version': '6.0', 'status': 'SUCCESS'}"
   Aug 23 17:49:44 gordon pywws-livelog[30946]: pywws.service.metoffice:OK
   Aug 23 17:49:45 gordon pywws-livelog[30946]: pywws.service.openweathermap:OK
   Aug 23 17:49:46 gordon pywws-livelog[30946]: pywws.service.cwop:OK
   Aug 23 17:49:46 gordon pywws-livelog[30946]: pywws.service.underground:server response "success"
   Aug 23 17:57:41 gordon pywws-livelog[30946]: pywws.weatherstation:setting sensor clock 5.33264
   Aug 23 17:57:41 gordon pywws-livelog[30946]: pywws.weatherstation:sensor clock drift 1.4672 1.08387
   Aug 23 18:00:25 gordon pywws-livelog[30946]: pywws.service.mastodon:OK
   Aug 23 18:00:26 gordon pywws-livelog[30946]: pywws.service.twitter:OK
   Aug 23 18:00:26 gordon pywws-livelog[30946]: pywws.service.sftp:OK
   jim@gordon:~ $

If you'd prefer to use a normal pywws log file the ``pywws.service`` file might look like this::

   [Unit]
   Description=pywws weather station live logging
   After=time-sync.target

   [Service]
   Type=simple
   User=pywws
   Restart=on-failure
   PermissionsStartOnly=true
   ExecStartPre=/bin/mkdir -p /var/log/pywws
   ExecStartPre=/bin/chown -R pywws:nogroup /var/log/pywws/
   ExecStart=/usr/local/bin/pywws-livelog -v -l /var/log/pywws/pywws.log /home/pywws/data/

In this example the log file is ``/var/log/pywws/pywws.log``.
The directory ``/var/log/pywws/`` might not exist after a reboot (e.g. if ``/var/log/`` has been moved to RAM disk to reduce SD card wear) so ``ExecStartPre`` is used to create it and transfer its ownership to the ``pywws`` user.
``PermissionsStartOnly=true`` ensures the ``ExecStartPre`` commands are run as root.

The udev_ system can be used to start the pywws service when the computer boots or the weather station is plugged into the USB port.
(It also stops pywws if the weather station is unplugged.)
Create a file ``/etc/udev/rules.d/39-weather-station.rules`` as follows::

   SUBSYSTEM=="usb" \
   , ATTRS{idVendor}=="1941" \
   , ATTRS{idProduct}=="8021" \
   , OWNER="pywws" \
   , TAG+="systemd" \
   , ENV{SYSTEMD_WANTS}="pywws.service"

This sets the owner of the weather station's USB port to ``pywws``, then adds ``pywws.service`` to the things ``systemd`` should be running.

Using pywws-livelog-daemon
^^^^^^^^^^^^^^^^^^^^^^^^^^

If you can't use systemd_ for some reason then the :py:mod:`pywws.livelogdaemon` program can be used to run pywws as a daemon, if you have the `python-daemon <https://pypi.python.org/pypi/python-daemon/>`_ library installed::

   pywws-livelog-daemon -v ~/weather/data ~/weather/data/pywws.log start

(Note that the log file is a required parameter, not an option.)
Unfortunately the python-daemon package appears not to be maintained, and I've had problems with it on some Linux versions.
You'll also need to setup something to start pywws automatically.

There are various ways of configuring a Linux system to start a program when the machine boots up.
Typically these involve putting a file in ``/etc/init.d/``.
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

.. _systemd: https://en.wikipedia.org/wiki/Systemd
.. _udev:    https://en.wikipedia.org/wiki/Udev
