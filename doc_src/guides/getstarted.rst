How to get started with pywws
=============================

#. Download and unpack the pywws software.

   Create a directory for all your weather related files and change to it. For example (on a Linux or similar operating system)::

      mkdir ~/weather
      cd ~/weather

   Visit the pywws website https://github.com/jim-easterbrook/pywws/downloads and download one of the .tar.gz or .zip files. Put it in your weather directory, then extract all the files, for example::

      tar zxvf pywws-12.10_r547.tar.gz

   or::

      unzip pywws-12.10_r547.zip

#. Install dependencies.

   * Python 2.4+ - http://python.org/ (Note: Python 3 is not supported.)

   * USB library option 1 (best for small systems such as routers):

     * libusb 0.1.12 - http://www.libusb.org/ (Note: libusb 1 is not supported.)
     * PyUSB 0.4.x - http://sourceforge.net/apps/trac/pyusb/
   * USB library option 2 (best for Linux PCs and Macs):

     * hidapi - https://github.com/signal11/hidapi
     * cython-hidapi - https://github.com/gbishop/cython-hidapi
     * cython - http://cython.org/

   You may be able to install these using your operating system's package manager. This is a lot easier than downloading and compiling the source files from the project websites. Note that some Linux distributions may use different names for some of the packages, e.g. in Ubuntu, pyusb is python-usb.

#. Test the weather station connection.

   Connect the weather station (if not already connected) then run the :py:mod:`TestWeatherStation` program. Change to the source code directory first. For example::

      cd ~/weather/pywws-12.10_r547/code
      python TestWeatherStation.py

   If everything is working correctly, this should dump a load of numbers to the screen, for example::

      0000 55 aa ff ff ff ff ff ff ff ff ff ff ff ff ff ff 05 20 01 51 11 00 00 00 81 00 00 0f 00 00 60 55
      0020 ea 27 a0 27 00 00 00 00 00 00 00 10 10 12 13 45 41 23 c8 00 32 80 47 2d 2c 01 2c 81 5e 01 1e 80
      0040 96 00 c8 80 a0 28 80 25 a0 28 80 25 03 36 00 05 6b 00 00 0a 00 f4 01 18 03 00 00 00 00 00 00 00
      0060 00 00 4e 1c 63 0d 2f 01 73 00 7a 01 47 80 7a 01 47 80 e4 00 00 00 71 28 7f 25 bb 28 bd 25 eb 00
      0080 0c 02 84 00 0e 01 e3 01 ab 03 dc 17 00 10 08 21 08 54 10 03 07 22 18 10 08 11 08 30 10 04 21 16
      00a0 26 08 07 24 17 17 08 11 01 06 10 09 06 30 14 29 09 01 06 07 46 09 06 30 14 29 09 01 06 07 46 08
      00c0 08 31 14 30 10 05 14 15 27 10 01 26 20 47 09 01 23 05 13 10 01 26 20 47 09 01 23 05 13 10 02 22
      00e0 11 06 10 02 22 11 06 08 07 07 19 32 08 12 13 22 32 08 09 07 08 48 01 12 05 04 43 10 02 22 14 43

   There are several reasons why this might not work. Most likely is a 'permissions' problem. This can be tested by running the command as root::

      sudo python TestWeatherStation.py

   If this works then you may be able to allow your normal user account to access the weather station by setting up a 'udev' rule. See the compatibility wiki page http://code.google.com/p/pywws/wiki/Compatibility for more details.

   If you have any other problem, please ask for help on the pywws mailing list: http://groups.google.com/group/pywws

#. Log your weather station data.

   First, choose a directory to store all your weather station data. This will be written to quite frequently, so a disk drive is preferable to a memory stick, as these have a limited number of writes. In most cases your home directory is suitable, for example::

      mkdir ~/weather/data

   This directory is referred to elsewhere in the pywws documentation as your data directory.

   Make sure your computer has the right date & time, and time zone, as these are used to label the weather station data. If you haven't already done so, it's worth setting up NTP to synchronise your computer to a 'time server'.

   Make sure your weather station has the correct offset between 'absolute' and 'relative' atmospheric pressure. See the instruction book for details on how to set this.

   The first time you run :py:mod:`pywws.LogData` it will create a configuration file in your data directory called 'weather.ini' and then stop. You need to edit the configuration file and change the line ``ws type = Unknown`` to ``ws type = 1080`` or ``ws type = 3080``. (If your weather station console displays solar illuminance you have a 3080 type, all others are 1080.) Then run :py:mod:`pywws.LogData` again. This may take several minutes, as it will copy all the data stored in your station's memory. The :py:mod:`pywws.LogData` program has a 'verbose' option that increases the amount of messages it displays while running. This is useful when running it manually, for example::

      python pywws/LogData.py -vvv ~/weather/data

   (Replace ``~/weather/data`` with your data directory, if it's different.)

   You should now have some data files you can look at. For example::

      more ~/weather/data/weather/raw/2012/2012-11/2012-11-16.txt

   (Replace the year, month and day with ones that you have data for.)

#. Convert old EasyWeather data (optional).

   If you had been running EasyWeather before deciding to use pywws, you can convert the data EasyWeather had logged to the pywws format. Find your EasyWeather.dat file and then convert it::

      python EWtoPy.py EasyWeather.dat ~/weather/data

#. Set some configuration options.

   After running :py:mod:`pywws.LogData` there should be a configuration file in your data directory called 'weather.ini'. Open this with a text editor. You should find something like the following::

      [fixed]
      ws type = 1080
      pressure offset = 7.4
      fixed block = {...}

      [config]
      logdata sync = 1

   The line ``[fixed]`` marks the start of a section (called '[fixed]'), and the following lines are entries in that section. The ``ws type`` entry can be set to ``1080`` or ``3080``. If your station's console displays illuminance and UV information, set it to ``3080``. The ``pressure offset`` entry stores the difference between absolute and relative atmospheric pressure that was read from the weather station. The ``fixed block`` entry stores a large amount of data from the station's 'fixed block' memory.

   You need to add a new entry in the ``[config]`` section called ``day end hour``. This tells pywws what convention you want to use when calculating daily summary data. In the UK, the 'meteorological day' is usually from 09:00 to 09:00 GMT (10:00 to 10:00 BST during summer), so I use a day end hour value of 9. In other countries a value of 24 (or 0) might be more suitable. Note that the value is set in local winter time. You should not need to change it when daylight savings time is in effect.

   After editing, your weather.ini file should look something like this::

      [fixed]
      ws type = 1080
      pressure offset = 7.4
      fixed block = {...}

      [config]
      logdata sync = 1
      day end hour = 9

   For more detail on the configuration file options, see :doc:`../guides/weather_ini`.

#. Process the raw data.

   :py:mod:`pywws.LogData` just copies the raw data from the weather station. To do something useful with that data you probably need hourly, daily and monthly summaries. These are created by the :py:mod:`pywws.Process` program. For example::

      python pywws/Process.py ~/weather/data

   You should now have some processed files to look at::

      more ~/weather/data/weather/daily/2012/2012-11-06.txt

   If you ever change your ``day end hour`` configuration setting, you will need to reprocess all your weather data. You can do this by running the :py:mod:`Reprocess` program::

      python Reprocess.py ~/weather/data

#. Set the weather station logging interval.

   Your weather station probably left the factory with a 30 minute logging interval. This enables the station to store about 11 weeks of data. Most pywws users set up their computers to read data from the station every hour, and only need the station to store enough data to cover computer failures. The recommended interval is 5 minutes, which still allows 2 weeks of storage. Use the :py:mod:`SetWeatherStation` program to set the interval::

      python SetWeatherStation.py -r 5

   You are now ready to set up regular or continuous logging, as described in :doc:`hourlylogging` or :doc:`livelogging`.

#. Read the documentation.

   The doc directory in your pywws source directory contains HTML and plain text versions of the documentation. The HTML files can be read with any web browser. Start with the index (:doc:`../index`) and follow links from there.

   Comments or questions? Please subscribe to the pywws mailing list http://groups.google.com/group/pywws and let us know.