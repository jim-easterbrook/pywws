pywws.LogData
=============

Introduction
------------

This program / module gets data from the weather station's memory and stores it to file. Each time it is run it fetches all data that is newer than the last stored data, so it only needs to be run every hour or so. As the weather station stores at least two weeks' readings, LogData.py could be run quite infrequently if you don't need up-to-date data.

There is no date or time information in the raw weather station data, so LogData.py waits until the "age" of the station's current data changes, then uses that time instant to calculate when the readings were stored. This process can be off by up to a minute, so stored data may not have uniform intervals between readings.

The weather station does have a real time clock (without seconds, unfortunately) but LogData.py ignores this and uses the computer's own clock instead. A networked computer should have its clock set accurately by `ntp <http://en.wikipedia.org/wiki/Network_Time_Protocol>`_, whereas the weather station's clock could be set to anything.

Detailed API
------------

.. automodule:: pywws.LogData

   .. rubric:: Functions

   .. autosummary::
   
      LogData
      main