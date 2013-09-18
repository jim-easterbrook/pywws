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

Dependencies
============

The list of other software that pywws depends on looks frighteningly long at first glance.
However, many of these packages won't be needed by most users.
What you need depends on what you want to do with pywws.
Remember, it's a "kit of parts" rather than a monolithic application.

You may be able to install most of these using your operating system's package manager.
This is a lot easier than downloading and compiling source files from the project websites.
Note that some Linux distributions use different names for some of the packages, e.g. in Ubuntu, pyusb is called python-usb.

Alternatively, you may be able to install more recent versions of some of the libraries from the `Python Package Index (PyPI) <http://pypi.python.org/pypi>`_.
I recommend installing `pip <http://www.pip-installer.org/>`_ (the package may be called python-pip) or `easy_install <http://peak.telecommunity.com/DevCenter/EasyInstall>`_.
These both simplify installation of software from PyPI.
For example, to install PyUSB from PyPI using the ``pip`` command::

  sudo pip install pyusb

Essential
---------

* `Python <http://python.org/>`_ version 2.5 or higher.

Python 3 is supported, but some things might not work properly.
If you find a problem with Python 3, please send a message to the `mailing list <http://groups.google.com/group/pywws>`_ or submit a `bug report on GitHub <https://github.com/jim-easterbrook/pywws/issues>`_.

USB library
^^^^^^^^^^^

To retrieve data from a weather station pywws needs a python library that allows it to communicate via USB.
There is a variety of USB libraries that can be used.
Not all of them are available on all computing platforms, which may restrict your choice.

On MacOS X the operating system's generic hid driver "claims" the weather station, which prevents libusb from working.
This restricts Mac users to option 3 or 4.

* USB library option 1 (preferred, except on MacOS)

  *  `PyUSB <http://sourceforge.net/apps/trac/pyusb/>`_ version 1.0
  *  `libusb <http://www.libusb.org/>`_ version 0.1 or version 1.0

* USB library option 2 (if PyUSB 1.0 is not available)

  *  `PyUSB <http://sourceforge.net/apps/trac/pyusb/>`_ version 0.4
  *  `libusb <http://www.libusb.org/>`_ version 0.1

* USB library option 3 (best for MacOS)

  *  `hidapi <https://github.com/signal11/hidapi>`_
  *  `ctypes <http://docs.python.org/2/library/ctypes.html>`_ (included with many Python installations)

* USB library option 4

  *  `hidapi <https://github.com/signal11/hidapi>`_
  *  `cython-hidapi <https://github.com/gbishop/cython-hidapi>`_
  *  `cython <http://cython.org/>`_

Graph drawing
-------------

The :py:mod:`pywws.Plot` module uses ``gnuplot`` to draw graphs.
If you want to produce graphs of weather data, e.g. to include in a web page, you need to install the ``gnuplot`` application:

*  `gnuplot <http://www.gnuplot.info/>`_ v4.2 or higher

Secure website uploading (sftp)
-------------------------------

The :py:mod:`pywws.Upload` module can use "ftp over ssh" (sftp) to upload files to your web-site.
Normal uploading just uses Python's standard modules, but if you want to use sftp you need to install these two modules:

*  `paramiko <https://github.com/paramiko/paramiko>`_
*  `pycrypto <http://www.dlitz.net/software/pycrypto/>`_

.. _dependencies-twitter:

Twitter updates
---------------

The :py:mod:`pywws.ToTwitter` module can be used to send weather status messages to Twitter.
Posting to Twitter requires all four of these modules:

*  `python-twitter <https://github.com/bear/python-twitter>`_ v0.8.6 or higher
*  `simplejson <https://github.com/simplejson/simplejson>`_
*  `python-oauth2 <https://github.com/simplegeo/python-oauth2>`_
*  `httplib2 <http://code.google.com/p/httplib2/>`_

.. versionchanged:: 13.06_r1023
   pywws previously used the `tweepy <https://github.com/tweepy/tweepy>`_ library instead of ``python-twitter`` and ``python-oauth2``.

To create new language translations
-----------------------------------

pywws can be configured to use languages other than English, and the documentation can also be translated into other languages.
See :doc:`../guides/language` for more information.
The ``gettext`` package is required to extract the strings to be translated and compile the translation files.

*  `gettext <http://www.gnu.org/s/gettext/>`_

To 'compile' the documentation
------------------------------

The documentation of pywws is written in "ReStructured text".
A program called ``Sphinx`` is used to convert this easy to write format into HTML for use with a web browser.
If you'd like to create a local copy of the documentation (so you don't have to rely on the online version, or to test a translation you're working on) you need to install ``Sphinx``.

*  `sphinx <http://sphinx-doc.org/>`_

Comments or questions? Please subscribe to the pywws mailing list http://groups.google.com/group/pywws and let us know.