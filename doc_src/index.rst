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

#####
pywws
#####

.. image:: img_1504.jpg
   :align: right

| Python software for USB Wireless WeatherStations
| http://pythonhosted.org/pywws
| http://jim-easterbrook.github.com/pywws/
| http://github.com/jim-easterbrook/pywws/

This document is available in the following languages (non-English versions may not be complete or up to date):

   * `English <../../en/html/index.html>`_
   * `Français <../../fr/html/index.html>`_ -- translated by Jacques Desroches
   * `Italiano <../../it/html/index.html>`_ -- translated by Edoardo

************
Introduction
************

pywws is a collection of Python scripts to read, store and process data from popular USB wireless weather stations such as Elecsa AstroTouch 6975, Watson W-8681, WH-1080PC, WH1080, WH1081, WH3080 etc. I assume any model that is supplied with the EasyWeather Windows software is compatible, but cannot guarantee this.

The software has been developed to run in a low power, low memory environment such as a router. It can be used to create graphs and web pages showing recent weather readings, typically updated every hour. It can also send data to services such as `Weather Underground <http://www.wunderground.com/>`_ and post messages to `Twitter <https://twitter.com/>`_.

I have written this software to meet my needs, but have tried to make it adaptable to other people's requirements. You may want to edit some or all of the modules, or write some new ones, to get it to do exactly what you want. One of the reasons for using Python is that it makes such alterations so easy. Don't be afraid, just jump in and have a go.

************
Requirements
************

The software you'll need to run pywws depends on what you plan to do with it.
You'll need Python 2.5 or later -- Python 3 is partially supported, some functionality depends on libraries that have not yet been ported to Python 3.

For more detail, see :doc:`essentials/dependencies`.

***********************
Getting a copy of pywws
***********************

The simplest way to obtain pywws is to use ``pip`` to install it directly from the `Python Package Index (PyPI) <http://pypi.python.org/pypi/pywws/>`_.
Note that this will probably require 'root' privileges, so will need to be run using ``sudo``::

   sudo pip install pywws

If you don't have root privileges, or don't want to install pywws into the system directories, you can download a zip or tar.gz file from PyPI and then extract the files into any convenient directory on your computer.

The PyPI files contain a snapshot release of the software - a new one is issued every few months.
If you'd like to keep up to date with latest developments of pywws, you should use ``git`` to clone the pywws repository::

   git clone https://github.com/jim-easterbrook/pywws.git

After doing so you can compile the documentation and language localisation files (which will require the ``sphinx`` and ``gettext`` dependencies)::

   cd pywws
   python setup.py msgfmt
   python setup.py build_sphinx

This is optional -- the documentation is available online and you might prefer to use pywws in English.

For more details, see :doc:`guides/getstarted`.

Upgrading pywws
===============

The method used to upgrade pywws depends on how you originally obtained it. If you downloaded a zip or tar.gz file, you just need to do the same again, with the new version, then delete your old download when you've finished setting up the new one. (Note that upgrading is much easier if you do not keep your templates, user modules and weather data in the same directory as the downloaded files.)
``git`` users just need to do a ``git pull`` command.
If you used ``pip`` you need to use the upgrade option::

   sudo pip install pywws -U

Some new versions of pywws have changed what's stored in the hourly, daily or monthly summary data files. These new versions are incompatible with processed data from earlier versions. The :py:mod:`pywws.Reprocess` module regenerates all the summary data. It should be run after any major upgrade.

*************
Documentation
*************

Documentation is included with pywws downloads, and is also available `online <http://pythonhosted.org/pywws>`_. A good starting place is :doc:`guides/getstarted` which describes in more detail how to install pywws.

If you have questions not answered in the documentation, please join the `pywws Google mailing list / discussion group <http://groups.google.com/group/pywws>`_ and ask there. Note that your first message to the group will not appear immediately -- new posters have to be approved by a moderator, to prevent spam messages.

Contents
========

.. toctree::
   :maxdepth: 2

   Licence <essentials/LICENCE>
   Dependencies <essentials/dependencies>
   Change log <essentials/CHANGELOG>
   User guides <guides/index>
   Python modules <api_index>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

*******
Credits
*******

I would not have been able to get any information from the weather station without access to the source of Michael Pendec's "wwsr" program. I am also indebted to Dave Wells for decoding the `weather station's "fixed block" data <http://www.jim-easterbrook.me.uk/weather/mm/>`_.

Last of all, a big thank you to all the pywws users who have helped with questions and suggestions, and especially to those who have translated pywws and its documentation into other languages.

********
Legalese
********

| pywws - Python software for USB Wireless WeatherStations.
| http://github.com/jim-easterbrook/pywws
| Copyright (C) 2008-13 Jim Easterbrook jim@jim-easterbrook.me.uk

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the `GNU General Public License <essentials/LICENCE.html>`_ along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA