.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-18  pywws contributors

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

pywws
#####

Python software for USB Wireless Weather Stations.

pywws is a collection of Python modules to read, store and process data from popular USB wireless weather stations such as Elecsa AstroTouch 6975, Watson W-8681, WH-1080PC, WH1080, WH1081, WH3080 etc. I assume any model that is supplied with the EasyWeather Windows software is compatible, but cannot guarantee this.

The software has been developed to run in a low power, low memory environment such as a `Raspberry Pi`_. It can be used to create graphs and web pages showing recent weather readings, typically updated every hour. It can also send "live" data to services such as `Weather Underground`_ and post messages to Twitter_.

The development version of pywws is hosted on GitHub.
   * https://github.com/jim-easterbrook/pywws

"Snapshot" releases of pywws are available from the `Python Package Index`_ (PyPI).
   * https://pypi.org/project/pywws/

Documentation is hosted on `Read the Docs`_.
   * http://pywws.readthedocs.io/

I have written this software to meet my needs, but have tried to make it adaptable to other people's requirements. You may want to edit some or all of the modules, or write some new ones, to get it to do exactly what you want. One of the reasons for using Python is that it makes such alterations so easy. Don't be afraid, just jump in and have a go.

Requirements
============

The software needed to run pywws depends on what you plan to do with it.
You'll need some of the following.

* Essential: Python_ 2.7 or 3 (also see `legacy version`_ below).
* Essential: USB library `python-libusb1`_ or PyUSB_ or, for MacOS, hidapi_ and a Python interface to it.
* Graph drawing: gnuplot_.
* Secure uploading to your web site: Paramiko_.
* Posting to Twitter_: `python-twitter`_ or Tweepy_.
* Posting to other web services: `python-requests`_.

For more detail, see the documentation - dependencies_.

Legacy version
--------------

If for some reason you are stuck with Python 2.5 or 2.6 a "`legacy branch`_" of pywws can be installed with pip and is available on GitHub. The most recent version of this branch is 18.4.1.

.. placeholder-credits

Credits
=======

I would not have been able to get any information from the weather station without access to the source of Michael Pendec's "wwsr" program. I am also indebted to Dave Wells for decoding the weather station's "`fixed block data`_".

Last of all, a big thank you to all the pywws users who have helped with questions and suggestions, and especially to those who have translated pywws and its documentation into other languages.

Legalese
========

| pywws - Python software for USB Wireless Weather Stations.
| https://github.com/jim-easterbrook/pywws
| Copyright (C) 2008-18  `pywws contributors`_

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the `GNU General Public License`_ along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA


.. _dependencies: http://pywws.readthedocs.io/en/latest/essentials/dependencies.html
.. _how to get started with pywws: http://pywws.readthedocs.io/en/latest/guides/getstarted.html
.. _pywws contributors: http://pywws.readthedocs.io/en/latest/copyright.html

.. _fixed block data: http://www.jim-easterbrook.me.uk/weather/mm/
.. _GNU General Public License: http://pywws.readthedocs.io/en/latest/essentials/LICENCE.html
.. _gnuplot: http://www.gnuplot.info/
.. _hidapi: http://www.signal11.us/oss/hidapi/
.. _legacy branch: https://pypi.org/project/pywws/18.4.1/
.. _Paramiko: https://pypi.org/project/paramiko/
.. _pip: https://pypi.org/project/pip/
.. _Python: https://www.python.org/
.. _Python Package Index: https://pypi.org/project/pywws/
.. _python-libusb1: https://pypi.org/project/libusb1/
.. _python-requests: https://pypi.org/project/requests/
.. _python-twitter: https://pypi.org/project/python-twitter/
.. _PyUSB: https://pypi.org/project/pyusb/
.. _pywws Google mailing list: http://groups.google.com/group/pywws
.. _Raspberry Pi: https://www.raspberrypi.org/
.. _Read the Docs: http://pywws.readthedocs.io/
.. _Tweepy: https://pypi.org/project/tweepy/
.. _Twitter: https://twitter.com/
.. _Weather Underground: https://www.wunderground.com/
