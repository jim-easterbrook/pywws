README
======

Python software for USB Wireless WeatherStations (pywws).
  http://code.google.com/p/pywws/

(C) 2008-11 Jim Easterbrook (jim@jim-easterbrook.me.uk)
derived from previous work by
Michael Pendec (michael.pendec@gmail.com) and
Svend Skafte (svend@skafte.net)

This software is not released through any official channels, and
therefore do not expect any support.

This software is in no way affiliated or related to
  http://www.foshk.com, Fine Offset Electronics Co.,LTD.

Licence terms:
    This softare is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This softare is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this softare; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Dependencies:

* libusb (http://libusb.sf.net) version 0.1.12
  (note: libusb 1 is not supported)
* Python (http://www.python.org/) version 2.4 or higher
  (note: Python 3 is not supported)
* PyUSB (http://pyusb.berlios.de/) version 0.4.x
* For graph drawing:

  * gnuplot (http://www.gnuplot.info/) v4.2 or higher
* For secure website uploading (sftp)

  * paramiko (http://www.lag.net/paramiko/)
  * pycrypto (http://www.dlitz.net/software/pycrypto/)
* For Twitter updates:

  * tweepy (http://code.google.com/p/tweepy/)
  * simplejson (http://pypi.python.org/pypi/simplejson)
* To create new language translations:

  * gettext (http://www.gnu.org/s/gettext/)

Many of these dependencies are available as packages for most Linux
distributions. This provides an easier way to install them than
downloading source from the project websites. Note that the package
names may be slightly different, e.g. python-usb instead of pyusb.

This software collection currently includes the following files:

* README.txt                 -- you are reading it!
* CHANGELOG.txt              -- development history
* LICENCE.txt                -- GNU General Public License

* TestWeatherStation.py      -- test communication with weather station
* Hourly.py                  -- run from cron or
* LiveLog.py                 -- run continuously
* EWtoPy.py                  -- converts EasyWeather.dat to DataStore format
* Reprocess.py               -- regenerates summary data
* TwitterAuth.py             -- authorise pywws to post to Twitter
* setup.py                   -- builds distributions
* makefile                   -- compiles language files and converts documentation from HTML to text

* pywws/\*.py                -- the pywws software modules
* example_graph_templates/\* -- example graph XML "recipes"
* example_templates/\*       -- example text templates
* example_modules/\*         -- example calibration modules
* doc/html/\*                -- HTML documentation of most of the above
* doc/txt/\*                 -- plain text documentation
* languages/\*               -- language source files and utility scripts

Upgrading from earlier versions:
  Back up your data, then run Reprocess.py to regenerate summary data.

Getting started:
  (For more detail, see doc/guides/getstarted: :doc:`../guides/getstarted`.)

#. Unzip / untar all the files to a convenient directory
#. Install Python, if not already installed
#. Install libusb, if not already installed
#. Install PyUSB, if not already installed

   Note: steps 2..4 may require installation of other software on some
   platforms, and you might have to compile / build some packages.
#. Run TestWeatherStation.py::

     python TestWeatherStation.py

   it should complain about not being able to connect to a weather station
#. Connect the weather station's USB port to your computer
#. Run TestWeatherStation.py again - you should get a load of data.
   If this fails it might be a 'permissions' problem. Try running as
   root::

     sudo python TestWeatherStation.py

   If this works then you
   may be able to set up a 'udev' rule for the weather station. See
   http://code.google.com/p/pywws/wiki/Compatibility for details.

   Try options to decode data and show history::

      python TestWeatherStation.py -d -h 5
#. Choose somewhere to store readings, e.g. /data/weather
#. Get some data from the weather station::

     python pywws/LogData.py /data/weather

   This will take a while the first time you run it, as it fetches
   all the data stored in the weather station.
#. If you have an EasyWeather.dat file, now is the time to convert it::

     python EWtoPy.py EasyWeather.dat /data/weather
#. Process the raw data to make hourly and daily summaries::

     python pywws/Process.py /data/weather
#. Generate some tables::

     python pywws/Template.py /data/weather \
             example_templates/24hrs.txt 24hrs.txt
     python pywws/Template.py /data/weather \
             example_templates/6hrs.txt 6hrs.txt
#. If you want to create graphs, install gnuplot, then::

     python pywws/Plot.py /data/weather /tmp \
             example_graph_templates/24hrs.png.xml 24hrs.png
     python pywws/Plot.py /data/weather /tmp \
             example_graph_templates/7days.png.xml 7days.png
#. Have a look at the files you've just made, then write a web page
   that incorporates them. (Use server side includes for the .txt
   files).
#. Edit /data/weather/weather.ini and add details of your website
   for example::

     [ftp]
     secure = False
     site = ftp.username.isp.co.uk
     user = username
     password = secret
     directory = public_html/weather/data/
#. Try uploading the files::

     python pywws/Upload.py /data/weather \
             24hrs.txt 6hrs.txt 24hrs.png 7days.png
#. If you want to upload to Twitter, install tweepy and simplejson,
   then::

     python TwitterAuth.py /data/weather

   This will open a web browser (or give you a URL) where you log in
   to your Twitter account and authorise pywws to post.
   Then::

     python pywws/Template.py /data/weather \
             example_templates/tweet.txt tweet.txt
     python pywws/ToTwitter.py /data/weather tweet.txt

   For more detail, see doc/guides/twitter: :doc:`../guides/twitter`.

#. If you want to upload to Weather Underground, try::

      python pywws/ToUnderground.py -vvv /data/weather

   You'll need to edit /data/weather/weather.ini with your Wunderground
   details, for example::

      [underground]
      password = undergroundpassword
      station = undergroundstation
#. Create directories for your graph templates and text templates, e.g.
   '~/weather/graph_templates/' and '~/weather/templates/', copy the
   templates you like to them, and run Hourly.py manually::

     python Hourly.py /data/weather

   You can now edit /data/weather/weather.ini to point to your template
   directories if Hourly.py didn't find them.
#. Set up a cron job to run Hourly.py every hour or every few hours or
   every day, according to your needs, at a minute or two past the hour.
#. Edit templates, weather.ini and other files to adjust everything to your
   taste.

Comments or questions? Please subscribe to the pywws mailing list
http://groups.google.com/group/pywws and let us know.
