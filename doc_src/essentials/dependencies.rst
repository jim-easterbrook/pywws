.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-14  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

Some of the requirements are Python packages that can be downloaded from the `Python Package Index (PyPI) <http://pypi.python.org/pypi>`_.
I recommend using `pip <http://www.pip-installer.org/>`_ to install these.

You should be able to install the remaining dependencies using your operating system's package manager.
This is a lot easier than downloading and compiling source files from the project websites.
Note that some Linux distributions use different names for some of the packages, e.g. in Ubuntu, pyusb is called python-usb.

Note: some of these libraries may have their own dependencies that you may need to install.
Follow the links to read more about each library's requirements.

Essential
---------

* `Python <http://python.org/>`_ version 2.5 or higher

Python 3 is supported, but some things might not work properly.
If you find a problem with Python 3, please send a message to the `mailing list <http://groups.google.com/group/pywws>`_ or submit a `bug report on GitHub <https://github.com/jim-easterbrook/pywws/issues>`_.

* `pip <http://www.pip-installer.org/>`_

You will probably be able to install pip with your system's package manager, where it may be called python-pip.
If not, download and run the ``get-pip.py`` file from the pip web site.
In either case you should immediately use pip to install the latest version of itself::

  sudo pip install --upgrade pip

USB library
^^^^^^^^^^^

To retrieve data from a weather station pywws needs a python library that allows it to communicate via USB.
There is a variety of USB libraries that can be used.
Not all of them are available on all computing platforms, which may restrict your choice.

Mac OS X
""""""""

On MacOS X the operating system's generic hid driver "claims" the weather station, which makes it very difficult to use any other USB interface.
Unfortunately, you will need to download and compile hidapi yourself.

*  `hidapi <http://www.signal11.us/oss/hidapi/>`_
*  `ctypes <http://docs.python.org/2/library/ctypes.html>`_ (your package manager may know it as python-ctypes)

If you can't install ctypes then you can try the Cython interface to hidapi instead:

*  `cython-hidapi <https://github.com/gbishop/cython-hidapi>`_
*  `cython <http://cython.org/>`_ (your package manager may know it as python-Cython)

Other systems
"""""""""""""

*  `libusb <http://www.libusb.org/>`_ version 0.1 or version 1.0 (should be available from the package manager)
*  `PyUSB <http://sourceforge.net/apps/trac/pyusb/>`_ version 1.0

::

  pip install pyusb==1.0.0b1

If you have problems with version 1 of PyUSB then version 0.4 can be used, provided you install version 0.1 of libusb.
Your system package manager should have both libraries.
As a last resort you can use hidapi -- see the Mac OS X instructions above.

Flexible timed tasks
--------------------

The :py:mod:`pywws.Tasks` module can do tasks at particular times and/or dates.
This requires the croniter library:

*  `croniter <https://pypi.python.org/pypi/croniter/>`_

::

  pip install croniter

Running as a daemon
-------------------

The :py:mod:`pywws.livelogdaemon` program runs pywws live logging as a proper UNIX daemon process.
It requires the python-daemon library:

*  `python-daemon <https://pypi.python.org/pypi/python-daemon/>`_

::

  pip install python-daemon

Graph drawing
-------------

The :py:mod:`pywws.Plot` module uses gnuplot to draw graphs.
If you want to produce graphs of weather data, e.g. to include in a web page, you need to install the gnuplot application:

*  `gnuplot <http://www.gnuplot.info/>`_ v4.2 or higher (should be available from the package manager)

Secure website uploading (sftp)
-------------------------------

The :py:mod:`pywws.Upload` module can use "ftp over ssh" (sftp) to upload files to your web-site.
Normal uploading just uses Python's standard modules, but if you want to use sftp you need to install these two modules:

*  `paramiko <https://github.com/paramiko/paramiko>`_
*  `pycrypto <http://www.dlitz.net/software/pycrypto/>`_

::

   sudo pip install pycrypto paramiko

.. _dependencies-twitter:

Twitter updates
---------------

The :py:mod:`pywws.ToTwitter` module can be used to send weather status messages to Twitter.
Posting to Twitter requires these modules:

*  `python-twitter <https://github.com/bear/python-twitter>`_ v1.0 or higher
*  `python-oauth2 <https://github.com/simplegeo/python-oauth2>`_

::

  sudo pip install python-twitter oauth2

**or**

*   `tweepy <https://github.com/tweepy/tweepy>`_ v2.0 or higher
*  `python-oauth2 <https://github.com/simplegeo/python-oauth2>`_

::

  sudo pip install tweepy oauth2

.. versionchanged:: 13.10_r1086
   reenabled use of ``tweepy`` library as an alternative to ``python-twitter``.
   ``python-oauth2`` is still required by :py:mod:`pywws.TwitterAuth`.

.. versionchanged:: 13.06_r1023
   pywws previously used the ``tweepy`` library instead of ``python-twitter`` and ``python-oauth2``.

.. _dependencies-translations:

To create new language translations
-----------------------------------

pywws can be configured to use languages other than English, as described in :doc:`../guides/language`.
The babel package is required to extract the strings to be translated and compile the translation files.

*  `babel <http://babel.pocoo.org/>`_

::

  sudo pip install babel

Translating the documentation also needs the sphinx-intl package.

*  `sphinx-intl <https://pypi.python.org/pypi/sphinx-intl>`_

::

  sudo pip install sphinx-intl

Copying files to or from Transifex is made easier with the transifex-client package.

*  `transifex-client <http://support.transifex.com/customer/portal/topics/440187-transifex-client>`_

::

  sudo pip install transifex-client

.. versionchanged:: 14.05.dev1209
   pywws previously used the gettext package.

.. _dependencies-compile-documentation:

To 'compile' the documentation
------------------------------

The documentation of pywws is written in "ReStructured text".
A program called Sphinx is used to convert this easy to write format into HTML for use with a web browser.
If you'd like to create a local copy of the documentation (so you don't have to rely on the online version, or to test a translation you're working on) you need to install Sphinx.

*  `Sphinx <http://sphinx-doc.org/>`_

::

  sudo pip install sphinx
