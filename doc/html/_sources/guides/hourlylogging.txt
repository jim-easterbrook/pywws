How to set up 'hourly' logging with pywws
=========================================

Introduction
------------

There are two quite different modes of operation with pywws. Traditionally the :doc:`../api/Hourly` program would be run at regular intervals (usually an hour) from cron. This is suitable for fairly static websites, but more frequent updates can be useful for sites such as Weather Underground (http://www.wunderground.com/). The newer :doc:`../api/LiveLog` program runs continuously and can upload data every 48 seconds.

Note that although this document (and the program name) refers to 'hourly' logging, you can run the Hourly.py program as often or as infrequently as you like, but don't try to run it more often than half your logging frequency. For example, if your logging interval is 10 minutes, don't run Hourly.py more often than every 20 minutes.

Getting started
---------------

First of all, you need to install pywws and make sure it can get data from your weather station. See :doc:`getstarted` for details.

Try running Hourly.py from the command line, with a high level of verbosity so you can see what's happening::

   python Hourly.py -vvv ~/weather/data

Within five minutes (assuming you have set a 5 minute logging interval) you should see a 'live_data new ptr' message, followed by fetching any new data from the weather station and processing it.

Configuring file locations
--------------------------

Open your weather.ini file with a text editor. You should have a ``[paths]`` section similar to the following (where ``xxx`` is your user name)::

  [paths]
  work = /tmp/weather
  templates = /home/xxx/weather/templates/
  graph_templates = /home/xxx/weather/graph_templates/

Edit these to suit your installation and preferences. ``work`` is a temporary directory used to store intermediate files, ``templates`` is the directory where you keep your text template files and ``graph_templates`` is the directory where you keep your graph template files. Don't use the pywws example directories for these, as they will get over-written when you upgrade pywws.

Copy your text and graph templates to the appropriate directories. You may find some of the examples provided with pywws useful to get started.

Configuring periodic tasks
--------------------------

In weather.ini you should have ``[logged]``, ``[hourly]``, ``[12 hourly]`` and ``[daily]`` sections similar to the following::

   [logged]
   services = []
   twitter = []
   plot = []
   text = []

   [hourly]
   ...

These specify what Hourly.py should do when it is run. Tasks in the ``[logged]`` section are done every time there is new logged data, tasks in the ``[hourly]`` section are done every hour, tasks in the ``[12 hourly]`` section are done twice daily and tasks in the ``[daily]`` section are done once per day.

The ``services`` entry is a list of online weather services to upload data to. The ``plot`` and ``text`` entries are lists of template files for plots and text files to be uploaded to your web site, and the ``twitter`` entry is a list of templates for messages to be posted to Twitter. Add the names of your template files and weather services to the appropriate entries, for example::

   [logged]
   services = ['underground', 'metoffice']
   twitter = []
   plot = []
   text = []

   [hourly]
   services = []
   twitter = ['tweet.txt']
   plot = ['7days.png.xml', '24hrs.png.xml', 'rose_24hrs.png.xml']
   text = ['24hrs.txt', '6hrs.txt', '7days.txt']

   [12 hourly]
   services = []
   twitter = []
   plot = []
   text = []

   [daily]
   services = []
   twitter = ['forecast.txt']
   plot = ['28days.png.xml']
   text = ['allmonths.txt']

You can test that all these are working by removing all ``last update`` lines from weather.ini then run Hourly.py again::

   python Hourly.py -v ~/weather/data

Run as a cron job
-----------------

Most UNIX/Linux systems have a 'cron' daemon that can run programs at certain times, even if you are not logged in to the computer. You edit a 'crontab' file to specify what to run and when to run  it. For example, to run Hourly.py every hour, at zero minutes past the hour::

   0 * * * *       python /home/jim/pywws/Hourly.py /home/jim/weather/data

This might work, but if it didn't you probably won't get any error messages to tell you what went wrong. It's much better to run a script that runs Hourly.py and then emails you any output it produces. Here's the script I use::

   #!/bin/sh
   #
   # weather station logger calling script

   if [ ! -d /data/weather/ ]; then
     exit
     fi

   log=/var/log/log-weather

   cd /home/jim/weather/devel
   python ./Hourly.py -v /data/weather >$log 2>&1

   # mail the log file
   /home/jim/scripts/email-log.sh $log "weather log"

You’ll need to edit this quite a lot to suit your file locations and so on, but it gives some idea of what to do.

Comments or questions? Please subscribe to the pywws mailing list http://groups.google.com/group/pywws and let us know.