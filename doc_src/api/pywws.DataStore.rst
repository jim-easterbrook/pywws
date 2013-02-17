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