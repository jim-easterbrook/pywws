Hourly
======

Introduction
------------

This script does nothing more than call other modules in sequence to get data from the weather station, process it, plot some graphs, generate some text files and upload the results to a web site.

The first time Hourly.py is run it will create the following entries in ``weather.ini``. Edit these to suit your installation and preferences. The "work" directory is used to store temporary files when plotting graphs. ::

  [paths]
  templates = ~/weather/templates/
  graph_templates = ~/weather/graph_templates/
  work = /tmp/weather

Once you have it working to your satisfaction, it's probably worth setting up a cron job to call it every hour or few hours or day, according to your needs. I run it on the hour, so my crontab entry is::

  0 * * * *       /home/jim/weather/Hourly.py

The only unusual feature of this script is that if any errors occur (such as not being able to connect to the website when uploading) then those parts will be repeated, up to three times in total.

Detailed API
------------

.. automodule:: Hourly
   
   .. rubric:: Functions

   .. autosummary::
   
      Hourly
      main