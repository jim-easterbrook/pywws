.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-15  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

Python programs and modules
===========================

Set up and configure pywws
--------------------------

.. autosummary::
   :toctree: api

   pywws.TestWeatherStation
   pywws.SetWeatherStation
   pywws.version
   pywws.Reprocess
   pywws.TwitterAuth
   pywws.USBQualityTest
   pywws.EWtoPy

Get data and process it
-----------------------

.. autosummary::
   :toctree: api

   pywws.Hourly
   pywws.LiveLog
   pywws.livelogdaemon

"Internal" modules
------------------

.. autosummary::
   :toctree: api

   pywws.Tasks
   pywws.LogData
   pywws.Process
   pywws.calib
   pywws.Plot
   pywws.WindRose
   pywws.Template
   pywws.Forecast
   pywws.ZambrettiCore
   pywws.Upload
   pywws.ToTwitter
   pywws.toservice
   pywws.YoWindow
   pywws.WeatherStation
   pywws.device_libusb1
   pywws.device_pyusb1
   pywws.device_pyusb
   pywws.device_ctypes_hidapi
   pywws.device_cython_hidapi
   pywws.DataStore
   pywws.TimeZone
   pywws.Localisation
   pywws.conversions
   pywws.Logger
   pywws.constants
