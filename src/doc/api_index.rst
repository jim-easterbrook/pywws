.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-20  pywws contributors

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

   pywws.testweatherstation
   pywws.setweatherstation
   pywws.version
   pywws.reprocess
   pywws.usbtest
   pywws.mergeewdata

Get data and process it
-----------------------

.. autosummary::
   :toctree: api

   pywws.hourly
   pywws.livelog
   pywws.livelogdaemon

.. _api-index-services:

Upload data to online "services"
--------------------------------

.. autosummary::
   :toctree: api

   pywws.service
   pywws.service.ftp
   pywws.service.sftp
   pywws.service.copy
   pywws.service.cwop
   pywws.service.metoffice
   pywws.service.mqtt
   pywws.service.openweathermap
   pywws.service.pwsweather
   pywws.service.temperaturnu
   pywws.service.underground
   pywws.service.weathercloud
   pywws.service.wetterarchivde
   pywws.service.windy
   pywws.service.twitter
   pywws.service.mastodon

"Internal" modules
------------------

.. autosummary::
   :toctree: api

   pywws.regulartasks
   pywws.logdata
   pywws.process
   pywws.calib
   pywws.plot
   pywws.windrose
   pywws.template
   pywws.forecast
   pywws.weatherstation
   pywws.device_libusb1
   pywws.device_pyusb1
   pywws.device_pyusb
   pywws.device_ctypes_hidapi
   pywws.device_cython_hidapi
   pywws.storage
   pywws.filedata
   pywws.timezone
   pywws.localisation
   pywws.conversions
   pywws.logger
   pywws.constants
