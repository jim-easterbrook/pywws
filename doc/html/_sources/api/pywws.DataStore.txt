pywws.DataStore
===============

Introduction
------------

This module is at the core of my weather station software. It stores data on disc, but without the overhead of a full scale database system. I have designed it to run on a small memory machine such as my Asus router. To minimise memory usage it only loads one day's worth of data at a time into memory.

From a "user" point of view, the data is accessed as a cross between a list and a dictionary. Each data record is indexed by a ``datetime`` object (dictionary behaviour), but records are stored in order and can be accessed as slices (list behaviour).

For example, to access the hourly data for Christmas day 2009, one might do the following::

  from datetime import datetime
  import DataStore
  hourly = DataStore.hourly_store('weather_data')
  for data in hourly[datetime(2009, 12, 25):datetime(2009, 12, 26)]:
      print data['idx'], data['temp_out']

The module provides five classes to store different data. ``data_store`` takes "raw" data from the weather station; ``calib_store``, ``hourly_store``, ``daily_store`` and ``monthly_store`` store processed data (see :doc:`pywws.Process`). All three are derived from the same ``core_store`` class, they only differ in the keys and types of data stored in each record.

Detailed API
------------

.. automodule:: pywws.DataStore
   
   .. rubric:: Functions

   .. autosummary::
   
      safestrptime
   
   .. rubric:: Classes

   .. autosummary::
   
      data_store
      calib_store
      hourly_store
      daily_store
      monthly_store
      core_store
      params