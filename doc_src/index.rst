#####
pywws
#####

.. image:: img_1504.jpg
   :align: right

| Python software for USB Wireless WeatherStations
| http://jim-easterbrook.github.com/pywws/
| http://github.com/jim-easterbrook/pywws/

This document is available in the following languages (non-English versions may not be complete or up to date):
   * `English <../../en/html/index.html>`_
   * `Français <../../fr/html/index.html>`_

************
Introduction
************

pywws is a collection of Python scripts to read, store and process data from popular USB wireless weather stations such as Elecsa AstroTouch 6975, Watson W-8681, WH-1080PC, WH1080, WH1081, WH3080 etc. I assume any model that is supplied with the EasyWeather Windows software is compatible, but cannot guarantee this.

The software has been developed to run in a low power, low memory environment such as a router. It can be used to create graphs and web pages showing recent weather readings, typically updated every hour. It can also send data to services such as `Weather Underground <http://www.wunderground.com/>`_ and post messages to `Twitter <https://twitter.com/>`_.

I have written this software to meet my needs, but have tried to make it adaptable to other people's requirements. You may want to edit some or all of the modules, or write some new ones, to get it to do exactly what you want. One of the reasons for using Python is that it makes such alterations so easy. Don't be afraid, just jump in and have a go.

************
Requirements
************

The software you'll need to run pywws depends on what you plan to do with it. In particular, there is a choice of USB library, to suit what's available on different operating systems.
   * `Python <http://python.org/>`_ version 2.4 or higher (note: Python 3 support is under development - some things may not work properly)
   * USB library option 1 (best for small systems such as routers):

     *  `PyUSB <http://sourceforge.net/apps/trac/pyusb/>`_ version 0.4.x
     *  `libusb <http://www.libusb.org/>`_ version 0.1.12
   * USB library option 2:

     *  `PyUSB <http://sourceforge.net/apps/trac/pyusb/>`_ version 1.0.x
     *  `libusb <http://www.libusb.org/>`_ version 0.1 or version 1.0
   * USB library option 3 (best for MacOS):

     *  `hidapi <https://github.com/signal11/hidapi>`_
     *  `cython-hidapi <https://github.com/gbishop/cython-hidapi>`_
     *  `cython <http://cython.org/>`_
   * For graph drawing:

     *  `gnuplot <http://www.gnuplot.info/>`_ v4.2 or higher
   * For secure website uploading (sftp)

     *  `paramiko <http://www.lag.net/paramiko/>`_
     *  `pycrypto <http://www.dlitz.net/software/pycrypto/>`_
   * For Twitter updates:

     *  `tweepy <http://code.google.com/p/tweepy/>`_
     *  `simplejson <http://pypi.python.org/pypi/simplejson>`_
   * To create new language translations:

     *  `gettext <http://www.gnu.org/s/gettext/>`_
   * To 'compile' the documentation:

     *  `sphinx <http://sphinx-doc.org/>`_

***********************
Getting a copy of pywws
***********************

The simplest way to obtain pywws is to download a zip or tar.gz file from the `Python Package Index (PyPI) <http://pypi.python.org/pypi/pywws/>`_ and then extract the files into a convenient directory on your computer. These files contain a snapshot release of the software - a new one is issued every few months.

You could also use ``pip`` to install pywws directly from PyPI::

   sudo pip install pywws

If you'd like to keep up to date with latest developments of pywws, you should use ``git`` to clone the pywws repository::

   git clone https://github.com/jim-easterbrook/pywws.git

After doing so you'll need to use ``make`` to compile the documentation and language localisation files (which will require the ``gettext`` and ``sphinx`` dependencies)::

   cd pywws
   make

*************
Documentation
*************

Documentation is included with pywws downloads, and is also available `online <http://jim-easterbrook.github.com/pywws/doc/html/>`_. A good starting place is the `how to get started guide <guides/getstarted.html>`_ which describes in more detail how to install pywws.

If you have questions not answered in the documentation, please join the `pywws Google mailing list / discussion group <http://groups.google.com/group/pywws>`_ and ask there.

Contents
========

.. toctree::
   :maxdepth: 2

   Licence <essentials/LICENCE>
   Change log <essentials/CHANGELOG>
   User guides <guides/index>
   Python programs and modules <api/index>

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
| http://jim-easterbrook.github.com/pywws/
| Copyright (C) 2008-12 Jim Easterbrook jim@jim-easterbrook.me.uk

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the `GNU General Public License <essentials/LICENCE.html>`_ along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA