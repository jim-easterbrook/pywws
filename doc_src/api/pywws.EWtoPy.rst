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

EWtoPy
======

Introduction
------------

This program converts data from the format used by the EasyWeather program supplied with the weather station to the format used by pywws. It is useful if you've been using EasyWeather for a while before discovering pywws.

The ``EasyWeather.dat`` file is only used to provide data from before the start of the pywws data. As your weather station has its own memory, you should run LogData.py before EWtoPy.py to minimise use of the EasyWeather.dat file.

EWtoPy.py converts the time stamps in EasyWeather.dat from local time to UTC. This can cause problems when daylight savings time ends, as local time appears to jump back one hour. The program attempts to detect this and correct the affected time stamps, but I have not been able to test this on a variety of time zones.

Detailed API
------------

.. automodule:: pywws.EWtoPy

   
   
   .. rubric:: Functions

   .. autosummary::
   
      main
