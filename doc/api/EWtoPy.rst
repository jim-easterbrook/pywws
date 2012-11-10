EWtoPy
======

Introduction
------------

This program converts data from the format used by the EasyWeather program supplied with the weather station to the format used by pywws. It is useful if you've been using EasyWeather for a while before discovering pywws.

The ``EasyWeather.dat`` file is only used to provide data from before the start of the pywws data. As your weather station has its own memory, you should run LogData.py before EWtoPy.py to minimise use of the EasyWeather.dat file.

EWtoPy.py converts the time stamps in EasyWeather.dat from local time to UTC. This can cause problems when daylight savings time ends, as local time appears to jump back one hour. The program attempts to detect this and correct the affected time stamps, but I have not been able to test this on a variety of time zones.

Detailed API
------------

.. automodule:: EWtoPy

   
   
   .. rubric:: Functions

   .. autosummary::
   
      main
