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

How to integrate pywws with various weather services 
====================================================

This guide gives brief instructions on how to use pywws with some other weather services and software.
It is not comprehensive, and some services (such as Twitter) are covered in more detail elsewhere.

YoWindow
--------

`YoWindow <http://yowindow.com/>`_ is a weather display widget that can display data from an internet source, or from your weather station.
To display data from your station pywws needs to write to a local file, typically every 48 seconds when new data is received.
This is easy to do:

 #. Stop all pywws software
 #. Copy the ``yowindow.xml`` example template to your text template directory.
 #. If you haven't already done so, edit ``weather.ini`` and set the ``local_files`` entry in the ``[paths]`` section to a suitable directory for your yowindow file.
 #. Add the yowindow template to the ``[live]`` tasks in ``weather.ini``. Set its flags to ``'L'`` so the result is copied to your local directory instead of being uploaded to an ftp site::

     [live]
     text = [('yowindow.xml', 'L')]
 #. Restart pywws live logging.

You can check the file is being updated every 48 seconds by using ``more`` or ``cat`` to dump it to the screen.

Finally configure yowindow to use this file.
See `<http://yowindow.com/pws_setup.php>`_ for instructions on how to do this.

Twitter
-------

See :doc:`twitter` for full instructions.

.. _guides-integration-other:

Other "services"
----------------

The remaining weather service uploads are handled by the :py:mod:`pywws.toservice` module.
See the module's documentation for general configuration options.
The following subsections give further information about some of the available services.

Citizen Weather Observer Program
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 14.02.dev1156

* Web site: http://www.wxqa.com/
* Create account: http://www.wxqa.com/SIGN-UP.html
* API: http://www.wxqa.com/faq.html
* Example ``weather.ini`` section::

    [cwop]
    designator = EW9999
    latitude = 5130.06N
    longitude = 00008.52E

  or, for radio hams::

    [cwop]
    designator = G4XXX
    passcode = xxxxxx
    latitude = 5130.06N
    longitude = 00008.52E

Note that the latitude and longitude must be in "LORAN" format and leading zeros are required.
See question 3 in the `CWOP FAQ <http://www.wxqa.com/faq.html>`_ for more information.

Licensed radio hams use their callsign as the designator and need a passcode.
They should use the service name ``cwop_ham`` instead of ``cwop`` when running :py:mod:`pywws.toservice` directly and in the ``weather.ini`` ``services`` entries.
(The same ``[cwop]`` config section is used for both.)

CWOP uploads are rate-limited by pywws, so you can safely add it to both the ``[live]`` and ``[logged]`` sections in ``weather.ini``.

The CWOP/APRS uploader is based on code by Marco Trevisan <mail@3v1n0.net>.

UK Met Office
^^^^^^^^^^^^^

* Web site: http://wow.metoffice.gov.uk/
* | Create account:
  | https://register.metoffice.gov.uk/WaveRegistrationClient/public/newaccount.do?service=weatherobservations
* API: http://wow.metoffice.gov.uk/support/dataformats#automatic
* Example ``weather.ini`` section::

    [metoffice]
    site id = 12345678
    aws pin = 987654

Open Weather Map
^^^^^^^^^^^^^^^^

* Web site: http://openweathermap.org/
* Create account: http://openweathermap.org/login
* API: http://openweathermap.org/API
* Example ``weather.ini`` section::

    [openweathermap]
    lat = 51.501
    long = -0.142
    alt = 10
    user = Elizabeth Windsor
    password = corgi
    id = Buck House

The default behaviour is to use your user name to identify the weather station.
However, it's possible for a user to have more than one weather station, so there is an undocumented ``name`` parameter in the API that can be used to identify the station.
This appears as ``id`` in ``weather.ini``.
Make sure you don't choose a name that is already in use.

PWS Weather
^^^^^^^^^^^

* Web site: http://www.pwsweather.com/
* Create account: http://www.pwsweather.com/register.php
* API based on WU protocol: `<http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol>`_
* Example ``weather.ini`` section::

    [pwsweather]
    station = ABCDEFGH1
    password = xxxxxxx

temperatur.nu
^^^^^^^^^^^^^

* Web site: http://www.temperatur.nu/
* Example ``weather.ini`` section::

    [temperaturnu]
    id = ???
    town = ???

Weather Underground
^^^^^^^^^^^^^^^^^^^

* Create account: http://www.wunderground.com/members/signup.asp
* API: `<http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol>`_
* Example ``weather.ini`` section::

    [underground]
    station = ABCDEFGH1
    password = xxxxxxx

Weather Underground "RapidFire" updates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Weather Underground has a second upload URL for real time updates as little as 2.5 seconds apart.
If you run pywws in 'live logging' mode (see :doc:`livelogging`) you can use this to send updates every 48 seconds, by adding 'underground_rf' to the ``[live]`` tasks section in ``weather.ini``::

 [live]
 services = ['underground_rf']

 [logged]
 services = ['underground']

Make sure you still have an 'underground' service in ``[logged]`` or ``[hourly]``.
This will ensure that 'catchup' records are sent to fill in any gaps if your station goes offline for some reason.

wetter.com
^^^^^^^^^^

* Web site: http://www.wetter.com/wetter_aktuell/wetternetzwerk/
* Example ``weather.ini`` section::

    [wetterarchivde]
    benutzername = ???
    passwort = ???
