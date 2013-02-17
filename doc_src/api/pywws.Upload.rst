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

pywws.Upload
============

Introduction
------------

This module uploads files to (typically) a website *via* ftp/sftp or copies files to a local directory (e.g. if you are running pywws on the your web server). Details of the upload destination are stored in the file ``weather.ini`` in your data directory. The only way to set these details is to edit the file. Run Upload.py once to set the default values, which you can then change. Here is what you're likely to find when you edit ``weather.ini``::

  [ftp]
  secure = False
  directory = public_html/weather/data/
  local site = False
  password = secret
  site = ftp.username.your_isp.co.uk
  user = username

These are, I hope, fairly obvious. The ``local site`` option lets you switch from uploading to a remote site to copying to a local site. If you set ``local site = True`` then you can delete the ``secure``, ``site``, ``user`` and ``password`` lines.

``directory`` is the name of a directory in which all the uploaded files will be put. This will depend on the structure of your web site and the sort of host you use. Your hosting provider should be able to tell you what ``site`` and ``user`` details to use. You should have already chosen a ``password``.

The ``secure`` option lets you switch from normal ftp to sftp (ftp over ssh). Some hosting providers offer this as a more secure upload mechanism, so you should probably use it if available.

Detailed API
------------

.. automodule:: pywws.Upload
   
   .. rubric:: Functions

   .. autosummary::
   
      Upload
      main
