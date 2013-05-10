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

Reprocess
=========

Introduction
------------

This program recreates the hourly, daily and monthly summary data that is created by the Process.py program. It should be run whenever you upgrade to a newer version of pywws.

The program is very simple to use::

  python Reprocess.py data_directory

where ``data_directory`` is the location of your stored data.

Detailed API
------------

.. automodule:: pywws.Reprocess
   
   .. rubric:: Functions

   .. autosummary::
   
      Reprocess
      main
