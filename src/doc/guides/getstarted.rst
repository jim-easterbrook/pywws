.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-16  pywws contributors

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

How to get started with pywws
=============================

Installation
------------

First of all you need to install Python and a USB library (to allow Python to access the weather station).
See :doc:`../essentials/dependencies` for more detail.

Create a directory for all your weather related files and change to it.
For example (on a Linux or similar operating system)::

   mkdir ~/weather
   cd ~/weather

Easy installation
^^^^^^^^^^^^^^^^^

The easiest way to install pywws is with the pip command::

   sudo pip install pywws

Upgrading pywws is also a one line command::

   sudo pip install -U pywws

Now you are ready to :ref:`test-weather-station`.

.. _getstarted-download:

Download and extract
^^^^^^^^^^^^^^^^^^^^

If you prefer not to use pip, or you want easy access to the pywws source files (e.g. to translate the documentation -- see :doc:`language`), you can download and extract the files into your weather directory.

Visit http://pypi.python.org/pypi/pywws/ and download one of the .tar.gz or .zip files. Put it in your weather directory, then extract all the files, for example::

   cd ~/weather
   tar zxvf pywws-14.03.dev1178.tar.gz

or::

   cd ~/weather
   unzip pywws-14.03.dev1178.zip

This should create a directory (called ``pywws-14.03.dev1178`` in this example) containing all the pywws source files.
It is convenient to create a soft link to this awkwardly named directory::

   cd ~/weather
   ln -s pywws-14.03.dev1178 pywws

Upgrading a downloaded snapshot is the same process as the first installation.
Download the .tar.gz or .zip file, extract its contents, then delete the soft link pointing to the old download and create one pointing to the new download.
Once you are satisfied the new version is working OK you can delete the old download entirely.

Clone the repository
^^^^^^^^^^^^^^^^^^^^

The PyPI files contain a snapshot release of the software - a new one is issued every few months.
If you want to use the very latest version of pywws, e.g. to work on fixing a bug, you can get all the files you need from the `GitHub repository <https://github.com/jim-easterbrook/pywws>`_.
Install git and use it to clone the repos::

   cd ~/weather
   git clone https://github.com/jim-easterbrook/pywws.git

To upgrade you use git to pull any changes::

   cd ~/weather/pywws
   git pull

Install pywws
^^^^^^^^^^^^^

If you have downloaded or cloned the pywws source files, you need to use setup.py to install it::

   cd ~/weather/pywws
   python setup.py compile_catalog
   python setup.py build
   sudo python setup.py install

The ``python setup.py compile_catalog`` step is only needed if you want to use pywws in a language other than English.
See :ref:`test-translation` for more detail.

Note to Python 3 users: this will generate and use Python 3 versions of the pywws software in ``~/weather/pywws/build/lib``.

Compile documentation (optional)
--------------------------------

If you'd like to have a local copy of the pywws documentation (and have downloaded the source or cloned the repo) you can "compile" the English documentation.
This requires the sphinx package::

   cd ~/weather/pywws
   python setup.py build_sphinx

Compiling the documentation in another language requires the additional step of compiling the translation files, which requires the sphinx-intl package.
For example, to compile the French documentation::

   cd ~/weather/pywws
   sphinx-intl build --locale-dir src/pywws/lang -l fr
   LANG=fr python setup.py build_sphinx

The compiled documentation should then be found at ``~/weather/pywws/doc/html/index.html``.
See :doc:`language` for more detail.

.. _test-weather-station:

Test the weather station connection
-----------------------------------

Now you're ready to test your pywws installation.
Connect the weather station (if not already connected) then run the :py:mod:`pywws.TestWeatherStation` module::

   pywws-testweatherstation

If everything is working correctly, this should dump a load of numbers to the screen, for example::

   0000 55 aa ff ff ff ff ff ff ff ff ff ff ff ff ff ff 05 20 01 51 11 00 00 00 81 00 00 0f 00 00 60 55
   0020 ea 27 a0 27 00 00 00 00 00 00 00 10 10 12 13 45 41 23 c8 00 32 80 47 2d 2c 01 2c 81 5e 01 1e 80
   0040 96 00 c8 80 a0 28 80 25 a0 28 80 25 03 36 00 05 6b 00 00 0a 00 f4 01 18 03 00 00 00 00 00 00 00
   0060 00 00 4e 1c 63 0d 2f 01 73 00 7a 01 47 80 7a 01 47 80 e4 00 00 00 71 28 7f 25 bb 28 bd 25 eb 00
   0080 0c 02 84 00 0e 01 e3 01 ab 03 dc 17 00 10 08 21 08 54 10 03 07 22 18 10 08 11 08 30 10 04 21 16
   00a0 26 08 07 24 17 17 08 11 01 06 10 09 06 30 14 29 09 01 06 07 46 09 06 30 14 29 09 01 06 07 46 08
   00c0 08 31 14 30 10 05 14 15 27 10 01 26 20 47 09 01 23 05 13 10 01 26 20 47 09 01 23 05 13 10 02 22
   00e0 11 06 10 02 22 11 06 08 07 07 19 32 08 12 13 22 32 08 09 07 08 48 01 12 05 04 43 10 02 22 14 43

There are several reasons why this might not work.
Most likely is a 'permissions' problem.
This can be tested by running the command as root::

   sudo pywws-testweatherstation

If this works then you may be able to allow your normal user account to access the weather station by setting up a `'udev' <http://en.wikipedia.org/wiki/Udev>`_ rule.
The exact method may depend on your Linux version, but this is typically done by creating a file ``/etc/udev/rules.d/39-weather-station.rules`` containing the following::

   ACTION!="add|change", GOTO="weatherstation_end"
   SUBSYSTEM=="usb", ATTRS{idVendor}=="1941", ATTRS{idProduct}=="8021", GROUP="weatherstation"
   LABEL="weatherstation_end"

Unplug and replug the station's USB connection to force ``udev`` to apply the new rule.
This allows any user in the group ``weatherstation`` to access the weather station.
You need to create this group and add your normal user account to it -- many Linux systems have a GUI for user and group management.

If you have any other problem, please ask for help on the pywws mailing list: http://groups.google.com/group/pywws

Set up your weather station
---------------------------

If you haven't already done so, you should set your weather station to display the correct relative atmospheric pressure.
(See the manual for details of how to do this.)
pywws gets the offset between relative and absolute pressure from the station, so this should be set before using pywws.

You can get the correct relative pressure from your location by looking on the internet for weather reports from a nearby station, ideally an official one such as an airport.
This is best done during calm weather when the pressure is almost constant over a large area.

Set the weather station logging interval
----------------------------------------

Your weather station probably left the factory with a 30 minute logging interval.
This enables the station to store about 11 weeks of data.
Most pywws users set up their computers to read data from the station every hour, or more often, and only need the station to store enough data to cover computer failures.
The recommended interval is 5 minutes, which still allows 2 weeks of storage.
Use :py:mod:`pywws.SetWeatherStation` to set the interval::

   pywws-setweatherstation -r 5

Note that the weather station will not start using the new interval until the current 30 minute logging period is finished.
This may cause "station is not logging data" errors when running pywws logging.
If this happens you need to wait until the 30 minute logging period ends.

Log your weather station data
-----------------------------

First, choose a directory to store all your weather station data.
This will be written to quite frequently, so a disk drive is preferable to a flash memory stick or card, as these have a limited number of writes.
In most cases your home directory is suitable, for example::

   mkdir ~/weather/data

This directory is referred to elsewhere in the pywws documentation as your data directory.

Make sure your computer has the right date & time, and time zone, as these are used to label the weather station data.
If you haven't already done so, it's worth setting up NTP to synchronise your computer to a 'time server'.

The first time you run :py:mod:`pywws.LogData` it will create a configuration file in your data directory called 'weather.ini' and then stop.
You need to edit the configuration file and change the line ``ws type = Unknown`` to ``ws type = 1080`` or ``ws type = 3080``.
(If your weather station console displays solar illuminance you have a 3080 type, all others are 1080.)
Then run :py:mod:`pywws.LogData` again.
This may take several minutes, as it will copy all the data stored in your station's memory.
The :py:mod:`pywws.LogData` program has a 'verbose' option that increases the amount of messages it displays while running.
This is useful when running it manually, for example::

   python -m pywws.LogData -vvv ~/weather/data

(Replace ``~/weather/data`` with your data directory, if it's different.)

You should now have some data files you can look at.
For example::

   more ~/weather/data/raw/2012/2012-12/2012-12-16.txt

(Replace the year, month and day with ones that you have data for.)

Convert old EasyWeather data (optional)
---------------------------------------

If you had been running EasyWeather before deciding to use pywws, you can convert the data EasyWeather had logged to the pywws format.
Find your EasyWeather.dat file and then convert it::

   python -m pywws.EWtoPy EasyWeather.dat ~/weather/data

Set some configuration options
------------------------------

After running :py:mod:`pywws.LogData` there should be a configuration file in your data directory called 'weather.ini'.
Open this with a text editor. You should find something like the following::

   [config]
   ws type = 1080
   logdata sync = 1
   pressure offset = 9.4

You need to add a new entry in the ``[config]`` section called ``day end hour``.
This tells pywws what convention you want to use when calculating daily summary data.
In the UK, the 'meteorological day' is usually from 09:00 to 09:00 GMT (10:00 to 10:00 BST during summer), so I use a day end hour value of 9.
In other countries a value of 24 (or 0) might be more suitable.
Note that the value is set in local winter time.
You should not need to change it when daylight savings time is in effect.

After editing, your weather.ini file should look something like this::

   [config]
   ws type = 1080
   logdata sync = 1
   pressure offset = 9.4
   day end hour = 9

You can also edit the ``pressure offset`` value to adjust how pywws calculates the relative (sea level) air pressure from the absolute value that the station measures.
If you change the pressure offset or day end hour in future, you must update all your stored data by running :py:mod:`pywws.Reprocess`.

For more detail on the configuration file options, see :doc:`../guides/weather_ini`.

.. versionchanged:: 13.10_r1082
   made ``pressure offset`` a config item.
   Previously it was always read from the weather station.

Process the raw data
--------------------

:py:mod:`pywws.LogData` just copies the raw data from the weather station.
To do something useful with that data you probably need hourly, daily and monthly summaries.
These are created by :py:mod:`pywws.Process`. For example::

   python -m pywws.Process ~/weather/data

You should now have some processed files to look at::

   more ~/weather/data/daily/2012/2012-12-16.txt

If you ever change your ``day end hour`` configuration setting, you will need to reprocess all your weather data.
You can do this by running :py:mod:`pywws.Reprocess`::

   python -m pywws.Reprocess ~/weather/data

You are now ready to set up regular or continuous logging, as described in :doc:`hourlylogging` or :doc:`livelogging`.

Read the documentation
----------------------

You're looking at it right now!
The :doc:`index` section is probably the most useful bit to read first, but the :doc:`../api_index` section has a lot more detail on the various pywws modules and commands.
