Python software for USB Wireless WeatherStations (pywws).

(C) 2008-10 Jim Easterbrook (jim@jim-easterbrook.me.uk)
derived from previous work by
Michael Pendec (michael.pendec@gmail.com) and
Svend Skafte (svend@skafte.net)

This software is not released through any official channels, and
therefore do not expect any support.

This software is in no way affiliated or related to
	www.foshk.com, Fine Offset Electronics Co.,LTD.

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
	libusb (http://libusb.sf.net)
	Python (http://www.python.org/) version 2.4 or higher
	PyUSB (http://pyusb.berlios.de/) version 0.4 or higher
	For graph drawing:
	  gnuplot (http://www.gnuplot.info/) v4.2 or higher
	For secure website uploading (sftp)
	  paramiko (http://www.lag.net/paramiko/)
	  pycrypto (http://www.dlitz.net/software/pycrypto/)
	For Twitter updates:
	  python-twitter
	    (http://code.google.com/p/python-twitter/) v0.6 or higher
	  simplejson (http://pypi.python.org/pypi/simplejson)
	To create new language translations:
	  msgfmt (from the gettext package) if installing on Linux

	Many of these dependencies are available as packages for most Linux
	distributions. This provides an easier way to install them than
	downloading source from the project websites.

This software collection currently contains the following files:
	README.txt		-- you are reading it!
	LICENCE.txt		-- GNU General Public License

	setup.py		-- compiles translation files
	WeatherStation.py	-- gets data from the weather station
	TestWeatherStation.py	-- test communication with weather station
	DataStore.py		-- stores readings in easy to access files
	LogData.py		-- saves recent readings to file
	Localisation.py		-- provides local language translations
	Hourly.py		-- run from cron
	Process.py		-- summarises raw data
	Plot.py			-- plots weather data using an XML recipe
	WindRose.py		-- draw a "wind rose" using an XML recipe
	Template.py		-- creates text data file based on a template
	Upload.py		-- uploads files to a web site by ftp or sftp
	ToTwitter.py		-- posts a message to a Twitter account
	ToUnderground.py	-- posts data to Weather Underground
	EWtoPy.py		-- converts EasyWeather.dat to DataStore format
	UpgradeFrom0-1.py	-- converts v0.1 datastore to current format
	Reprocess.py		-- regenerates summary data
	AutoDoc.py		-- generates extra HTML documentation

	example_graph_templates/*
				-- example graph XML "recipes"
	example_templates/*	-- example text templates
	doc/*			-- HTML documentation of most of the above
	languages/*		-- language source files and utility scripts

Upgrading from earlier versions:
	Back up your data, then run one of the following, depending on
	which version of pywws you have been using:
	v0.1 : run UpgradeFrom0-1.py to translate data file format
	v0.2 or later : run Reprocess.py to regenerate summary data

Preparation:
	Unlike some other weather station software, this software relies on
	the weather station base unit's stored readings. New weather stations
	have the logging interval set to 30 minutes, which allows about 11
	weeks data to be stored. Before using this software I think it is
	worth changing the logging interval to 5 minutes, which will still
	allow for 2 weeks to be stored.

	Unfortunately, you need the EasyWeather software (Windows only) to set
	the logging interval. Luckily you only need to do it once.

	The second weather station adjustment to make is the offset between
	absolute and relative pressure. See the instruction book for details.

Getting started:
  1/ Unzip / untar all the files to a convenient directory
  2/ Install Python, if not already installed
  3/ Install libusb, if not already installed
  4/ Install PyUSB, if not already installed
  Note: steps 2..4 may require installation of other software on some
  platforms, and you might have to compile / build some packages.
  5/ Run "python TestWeatherStation.py" - it should complain about not
     being able to connect to a weather station
  6/ Connect weather station's USB port to computer
  7/ Run TestWeatherStation.py again - you should get a load of data.
     If this fails it might be a 'permissions' problem. Try running as
     root: "sudo python TestWeatherStation.py"
     7a/ Try options to decode data and show history:
         "python TestWeatherStation.py -d -h 5"
  8/ Run "python AutoDoc.py" to create extra documentation of the
     software.
  9/ Choose somewhere to store readings, e.g. /data/weather
  10/ Get some data from the weather station:
      "python LogData.py /data/weather"
      This will take a while the first time you run it, as it fetches
      all the data stored in the weather station.
  11/ If you have an EasyWeather.dat file, now is the time to convert it:
      "python EWtoPy.py EasyWeather.dat /data/weather"
  12/ Process the raw data to make hourly and daily summaries:
      "python Process.py /data/weather"
  13/ Generate some tables:
      "python Template.py /data/weather example_templates/24hrs.txt 24hrs.txt"
      "python Template.py /data/weather example_templates/6hrs.txt 6hrs.txt"
  14/ If you want to create graphs, install gnuplot, then:
      "python Plot.py /data/weather /tmp \
		example_graph_templates/24hrs.png.xml 24hrs.png"
      "python Plot.py /data/weather /tmp \
		example_graph_templates/7days.png.xml 7days.png"
  15/ Have a look at the files you've just made, then write a web page
      that incorporates them. (Use server side includes for the .txt
      files).
  16/ Edit /data/weather/weather.ini and add details of your website
      for example:
  	[ftp]
  	secure = False
  	site = ftp.username.isp.co.uk
  	user = username
  	password = secret
  	directory = public_html/weather/data/
  17/ Try uploading the files:
      "python Upload.py /data/weather 24hrs.txt 6hrs.txt 24hrs.png 7days.png"
  18/ If you want to upload to Twitter, install python-twitter and simplejson
      then:
      "python Template.py /data/weather example_templates/tweet.txt tweet.txt"
      "python ToTwitter.py /data/weather tweet.txt"
      You'll need to edit /data/weather/weather.ini with your Twitter
      account details, for example:
        [twitter]
        username = twitterusername
        password = twitterpassword
  19/ If you want to upload to Weather Underground, try:
      "python ToUnderground.py -vvv /data/weather"
      You'll need to edit /data/weather/weather.ini with your Wunderground
      details, for example:
        [underground]
        password = undergroudpassword
        station = undergroundstation
  20/ Create directories for your graph templates and text templates, e.g.
      '~/weather/graph_templates/' and '~/weather/templates/', copy the
      templates you like to them, and run Hourly.py manually:
      "python Hourly.py /data/weather"
      You can now edit /data/weather/weather.ini to point to your template
      directories if Hourly.py didn't find them.
  21/ Set up a cron job to run Hourly.py every hour or every few hours or
      every day, according to your needs, at a minute or two past the hour.
  22/ Edit templates, Hourly.py and other files to adjust everything to your
      taste.

Comments or questions? Please subscribe to the pywws mailing list
http://groups.google.com/group/pywws and let us know.

Changes in v10.06:
	1/ Improved localisation code.
	2/ Minor bug fixes.
	3/ Added Y axis label angle control to plots.

Changes in v10.04:
	1/ Changed version numbering to year.month.
	2/ Allowed "upload" to a local directory instead of ftp site.
	3/ Added "calc" option to text templates (Template.py).
	4/ Added -v / --verbose option to Hourly.py to allow silent operation.
	5/ Added internationalisation / localisation of some strings.
	6/ Made 'raw' data available to text templates.
	7/ Added ability to upload to Weather Underground.
	8/ Added dual axis and cumulative graph capability.

Changes in v0.9:
	1/ Added lowest daytime max and highest nighttime min temperatures
	   to monthly data.
	2/ Added average temperature to daily and monthly data.
	3/ Added 'terminal' element to Plot.py templates for greater control
	   over output appearance.
	4/ Added 'command' element to Plot.py templates for even more
	   control, for advanced users.
	5/ Added secure upload option.
	6/ Minor speed improvements.

Changes in v0.8:
	1/ Added meteorological day end hour user preference
	2/ Attempts at Windows compatibility
	3/ Corrected decoding of wind data at speeds over 25.5 m/s
	4/ Improved speed with new data caching strategy

Changes in v0.7:
	1/ Several bug fixes, mostly around new weather stations with not
	   much data
	2/ Added min & max temperature extremes to monthly data
	3/ Added template and workspace directory locations to weather.ini
	4/ Increased versatility of Plot.py with layout and title elements

Changes in v0.6:
	1/ Added monthly data
	2/ Changed 'pressure' to 'abs_pressure' or 'rel_pressure'

Changes in v0.5:
	1/ Small bug fixes.
	2/ Added start time to daily data
	3/ Replaced individual plot programs with XML "recipe" system

Changes in v0.4:
	1/ Can post brief messages to Twitter.
	2/ Now time zone aware. Uses UTC for data indexing and local time
	   for graphs and text data files.

Changes in v0.3:
	1/ Now uses templates to generate text data
	2/ Added 28 day plot
	3/ Minor efficiency improvements
	4/ Improved documentation

Changes in v0.2:
	1/ Now uses Python csv library to read and write data
	2/ Creates hourly and daily summary files
	3/ Includes rain data in graphs

Still to come, possibly:
	1/ Monthly and yearly graphs and tables?
	2/ Better documentation (but don't hold your breath)
	3/ Select units (e.g. mph - km/h - m/s) in config file

If you've got this software up and running, do let me know what you think.
Email jim@jim-easterbrook.me.uk
http://code.google.com/p/pywws/

