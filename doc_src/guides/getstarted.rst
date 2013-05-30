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

How to get started with pywws
=============================

Install dependencies
--------------------

* Python 2.5+ - http://python.org/ (Note: Python 3 support is under development.)

* USB library option 1 (preferred, except on MacOS):

  * PyUSB 1.0 - http://sourceforge.net/apps/trac/pyusb/
  * libusb 0.1 or 1.0 - http://www.libusb.org/
* USB library option 2 (if PyUSB 1.0 is not available):

  * PyUSB 0.4 - http://sourceforge.net/apps/trac/pyusb/
  * libusb 0.1 - http://www.libusb.org/
* USB library option 3 (best for MacOS):

  * hidapi - https://github.com/signal11/hidapi
  * ctypes - http://docs.python.org/2/library/ctypes.html
* USB library option 4:

  * hidapi - https://github.com/signal11/hidapi
  * cython-hidapi - https://github.com/gbishop/cython-hidapi
  * cython - http://cython.org/

You may be able to install most of these using your operating system's package manager.
This is a lot easier than downloading and compiling source files from the project websites.
Note that some Linux distributions may use different names for some of the packages, e.g. in Ubuntu, pyusb is python-usb.

In addition to the above, I recommend installing `pip <http://www.pip-installer.org/>`_ (the package may be called python-pip) or `easy_install <http://peak.telecommunity.com/DevCenter/EasyInstall>`_.
These both simplify installation of software from the `Python Package Index (PyPI) <http://pypi.python.org/pypi>`_.
For example, PyUSB can be installed from PyPI using the ``pip`` command::

   sudo pip install pyusb

Download the pywws software
---------------------------

Create a directory for all your weather related files and change to it.
For example (on a Linux or similar operating system)::

   mkdir ~/weather
   cd ~/weather

You can install pywws directly from PyPI using ``pip`` or ``easy_install``, or you can download and extract the files into your weather directory.
This has the advantage that you can easily read the Python modules and other files.
It also allows you to run pywws software without the 'root' privileges usually needed to install software.

Easy installation
^^^^^^^^^^^^^^^^^

This is a simple one line command::

   sudo pip install pywws

The directories everything gets installed to depend on your operating system and Python version.
The pywws modules are installed in the 'site-packages' directory (e.g. ``/usr/lib/python2.7/site-packages``).
Typically the scripts are installed in ``/usr/bin``, and the example files are installed in ``/usr/share/pywws``, but other directories (such as ``/usr/local/share``) could be used.

Download and extract
^^^^^^^^^^^^^^^^^^^^

You can either download a snapshot release from PyPI, or you can use ``git`` to get the most up to date development version of pywws.

To download a snapshot, visit http://pypi.python.org/pypi/pywws/ and download one of the .tar.gz or .zip files. Put it in your weather directory, then extract all the files, for example::

   cd ~/weather
   tar zxvf pywws-12.11_95babb0.tar.gz

or::

   cd ~/weather
   unzip pywws-12.11_95babb0.zip

This should create a directory (called ``pywws-12.11_95babb0`` in this example) containing all the pywws source files.
It is convenient to create a soft link to this awkwardly named directory::

   cd ~/weather
   ln -s pywws-12.11_95babb0 pywws

Alternatively, to get the latest development version of pywws use ``git clone``, then use ``setup.py`` to compile the language files and documentation::

   cd ~/weather
   git clone https://github.com/jim-easterbrook/pywws.git
   cd pywws
   python setup.py msgfmt
   python setup.py build_sphinx

After downloading and extracting, or cloning the repos, you can then use ``setup.py`` to build and install everything::

   cd ~/weather/pywws
   python setup.py build
   sudo python setup.py install

This is optional, and installs into the same directories as using ``pip`` would.
If you don't do this installation process, you will only be able to run pywws modules from your pywws directory.

(Python 3 users only) Translate pywws to Python 3
-------------------------------------------------

If your default Python version is 3.x and you installed pywws using ``pip``, or ran ``python setup.py install``, the code will already have been translated from Python 2 to Python 3 as part of the installation process.
If not, you need to use setup.py to do the translation and create a Python 3 installation::

   cd ~/weather/pywws
   rm -Rf build
   python3 setup.py build
   sudo python3 setup.py install

Test the weather station connection
-----------------------------------

Finally you're ready to test your pywws installation.
Connect the weather station (if not already connected) then run the :py:mod:`pywws.TestWeatherStation` module.
If you have downloaded but not installed pywws, then don't forget to change to the pywws directory first.
For example::

   cd ~/weather/pywws
   python -m pywws.TestWeatherStation

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

   sudo python -m pywws.TestWeatherStation

If this works then you may be able to allow your normal user account to access the weather station by setting up a 'udev' rule.
See the compatibility wiki page http://code.google.com/p/pywws/wiki/Compatibility for more details.

If you have any other problem, please ask for help on the pywws mailing list: http://groups.google.com/group/pywws

Set up your weather station
---------------------------

If you haven't already done so, set your weather station to display the correct relative atmospheric pressure.
(See the manual for details of how to do this.)
pywws gets the offset between relative and absolute pressure from the station, so this needs to be set before using pywws.

You can get the correct relative pressure from your location by looking on the internet for weather reports from a nearby station, ideally an official one such as an airport.
This is best done during calm weather when the pressure is almost constant over a large area.

If you change the offset at any time, you can update all your stored data by running :py:mod:`pywws.Reprocess`.

Set the weather station logging interval
----------------------------------------

Your weather station probably left the factory with a 30 minute logging interval.
This enables the station to store about 11 weeks of data.
Most pywws users set up their computers to read data from the station every hour, or more often, and only need the station to store enough data to cover computer failures.
The recommended interval is 5 minutes, which still allows 2 weeks of storage.
Use :py:mod:`pywws.SetWeatherStation` to set the interval::

   python -m pywws.SetWeatherStation -r 5

Log your weather station data
-----------------------------

First, choose a directory to store all your weather station data.
This will be written to quite frequently, so a disk drive is preferable to a memory stick, as these have a limited number of writes.
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

   more ~/weather/data/weather/raw/2012/2012-12/2012-12-16.txt

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
   day end hour = 9

For more detail on the configuration file options, see :doc:`../guides/weather_ini`.

Process the raw data
--------------------

:py:mod:`pywws.LogData` just copies the raw data from the weather station.
To do something useful with that data you probably need hourly, daily and monthly summaries.
These are created by :py:mod:`pywws.Process`. For example::

   python -m pywws.Process ~/weather/data

You should now have some processed files to look at::

   more ~/weather/data/weather/daily/2012/2012-12-16.txt

If you ever change your ``day end hour`` configuration setting, you will need to reprocess all your weather data.
You can do this by running :py:mod:`pywws.Reprocess`::

   python -m pywws.Reprocess ~/weather/data

You are now ready to set up regular or continuous logging, as described in :doc:`hourlylogging` or :doc:`livelogging`.

Read the documentation
----------------------

The doc directory in your pywws source directory contains HTML and plain text versions of the documentation (unless you did a direct installation with ``pip``).
The HTML files can be read with any web browser.
Start with the index (:doc:`../index`) and follow links from there.

Comments or questions? Please subscribe to the pywws mailing list http://groups.google.com/group/pywws and let us know.