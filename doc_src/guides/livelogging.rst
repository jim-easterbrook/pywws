How to set up 'live' logging with pywws
=======================================

Introduction
------------

There are two quite different modes of operation with pywws. Traditionally the :doc:`../api/Hourly` program would be run at regular intervals (usually an hour) from cron. This is suitable for fairly static websites, but more frequent updates can be useful for sites such as Weather Underground (http://www.wunderground.com/). The newer :doc:`../api/LiveLog` program runs continuously and can upload data every 48 seconds.

Getting started
---------------

First of all, you need to install pywws and make sure it can get data from your weather station. See :doc:`getstarted` for details.

Try running LiveLog.py from the command line, with a high level of verbosity so you can see what's happening::

   python LiveLog.py -vvv ~/weather/data

Within five minutes (assuming you have set a 5 minute logging interval) you should see a 'live_data new ptr' message, followed by fetching any new data from the weather station and processing it. Let LiveLog.py run for a minute or two longer, then kill the process by typing '<Ctrl>C'.

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

In weather.ini you should have a ``[live]`` section similar to the following::

   [live]
   services = []
   twitter = []
   plot = []
   text = []

This section specifies what pywws should do every time it gets a new reading from the weather station, i.e. every 48 seconds. The ``services`` entry is a list of online weather services to upload data to, e.g. ``['underground']``. The ``plot`` and ``text`` entries are lists of template files for plots and text files to be uploaded to your web site, and the ``twitter`` entry is a list of templates for messages to be posted to Twitter. You should probably leave all of these blank except for ``services``.

If you use YoWindow (http://yowindow.com/) you can add an entry to the ``[live]`` section to specify your YoWindow file, e.g.::

   [live]
   yowindow = /home/jim/data/yowindow.xml
   services = ['underground']
   ...

If you don't already have them, create four more sections in your weather.ini file: ``[logged]``, ``[hourly]``, ``[12 hourly]`` and ``[daily]``. These sections should have similar entries to the ``[live]`` section, and specify what to do every time data is logged (5 to 30 minutes, depending on your logging interval), every hour, twice daily and once per day. Add the names of your template files to the appropriate entries, for example::

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

Run in the background
---------------------

In order to have LiveLog.py carry on running after you finish using your computer it needs to be run as a 'background job'. On most Linux / UNIX systems you can do this by putting an ampersand ('&') at the end of the command line. For example::

   python LiveLog.py ~/weather/data &

However, it would be useful to know what went wrong if the program crashes for any reason. LiveLog.py can store its messages in a log file, specified with the -l option::

   python LiveLog.py -v -l ~/weather/data/pywws.log ~/weather/data &

Automatic restarting
--------------------

There are various ways of configuring a Linux system to start a program when the machine boots up. Typically these involve putting a file in /etc/init.d/, which requires root privileges. A slightly harder problem is ensuring a program restarts if it crashes. My solution to both problems is to run the following script from cron, every hour. ::

   #!/bin/sh

   pidfile=/var/run/pywws.pid
   datadir=/data/weather
   logfile=$datadir/live_logger.log

   # exit if process is running
   [ -f $pidfile ] && kill -0 `cat $pidfile` && exit

   # email last few lines of the logfile to see why it died
   if [ -f $logfile ]; then
     log=/var/log/log-weather
     tail -40 $logfile >$log
     /home/jim/scripts/email-log.sh $log "weather log"
     rm $log
     fi

   # restart process
   python /home/jim/weather/devel/LiveLog.py -v -l $logfile $datadir &
   echo $! >$pidfile

This stores the process id of the running LiveLog.py in pidfile. If the process is running, the script does nothing. If the process has crashed, it emails the last 40 lines of the log file to me (using a script that creates a message and passes it to sendmail) and then restarts LiveLog.py. You'll need to edit this quite a lot to suit your file locations and so on, but it gives some idea of what to do.

Comments or questions? Please subscribe to the pywws mailing list http://groups.google.com/group/pywws and let us know.