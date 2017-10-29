.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-15  pywws contributors

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
    template = default

    [logged]
    services = ['cwop', 'underground']

    [live]
    services = ['cwop', 'underground_rf']

  or, for radio hams::

    [cwop]
    designator = G4XXX
    passcode = xxxxxx
    latitude = 5130.06N
    longitude = 00008.52E
    template = default

    [logged]
    services = ['cwop_ham', 'underground']

    [live]
    services = ['cwop_ham', 'underground_rf']

Note that the latitude and longitude must be in "LORAN" format and leading zeros are required.
See question 3 in the `CWOP FAQ <http://www.wxqa.com/faq.html>`_ for more information.

Licensed radio hams use their callsign as the designator and need a passcode.
They should use the service name ``cwop_ham`` instead of ``cwop`` when running :py:mod:`pywws.toservice` directly and in the ``weather.ini`` ``services`` entries.
(The same ``[cwop]`` config section is used for both.)

CWOP uploads are rate-limited by pywws, so you can safely add it to both the ``[live]`` and ``[logged]`` sections in ``weather.ini``.

The CWOP/APRS uploader is based on code by Marco Trevisan <mail@3v1n0.net>.

MQTT
^^^^

.. versionadded:: 14.12.0.dev1260

MQTT is a "message broker" system, typically running on ``localhost`` or another computer in your home network.
Use of MQTT with pywws requires an additional library.
See :ref:`Dependencies - MQTT <dependencies-mqtt>` for details.

* MQTT: http://mqtt.org/
* Mosquitto (a lightweight broker): http://mosquitto.org/
* Example ``weather.ini`` section::

    [mqtt]
    topic = /weather/pywws
    hostname = localhost
    port = 1883
    client_id = pywws
    retain = True
    auth = False
    user = unknown
    password = unknown
    template = default
    multi_topic = False

    [logged]
    services = ['mqtt', 'underground']

pywws will publish a JSON string of the data specified in the ``mqtt_template_1080.txt`` file.
This data will be published to the broker running on hostname, with the port number specified.
(An IP address can be used instead of a host name.)
``client_id`` is a note of who published the data to the topic.
``topic`` can be any string value, this needs to be the topic that a subscriber is aware of.

``retain`` is a boolean and should be set to ``True`` or ``False`` (or left at the default ``unknown``).
If set to ``True`` this will flag the message sent to the broker to be retained.
Otherwise the broker discards the message if no client is subscribing to this topic.
This allows clients to get an immediate response when they subscribe to a topic, without having to wait until the next message is published.

``auth``, ``user`` and ``password`` can be used for MQTT authentication.

``multi_topic`` is a boolean and should be set to ``True`` or ``False``.
If set to ``True`` pywws will also publish all the data each as separate subtopics of the configured ``topic``;
i.e., with the ``topic`` set to /weather/pywws pywws will also publish the outside temperature to ``/weather/pywws/temp_out`` and the inside temperature to ``/weather/pywws/temp_in``.  

If these aren't obvious to you it's worth doing a bit of reading around MQTT.
It's a great lightweight messaging system from IBM, recently made more popular when Facebook published information on their use of it.

This has been tested with the Mosquitto Open Source MQTT broker, running on a Raspberry Pi (Raspian OS).
TLS (mqtt data encryption) is not yet implemented.

Thanks to Matt Thompson for writing the MQTT code and to Robin Kearney for adding the retain and auth options.

UK Met Office
^^^^^^^^^^^^^

* Web site: http://wow.metoffice.gov.uk/
* Create account: https://register.metoffice.gov.uk/WaveRegistrationClient/public/newaccount.do?service=weatherobservations
* API: http://wow.metoffice.gov.uk/support/dataformats#automatic
* Example ``weather.ini`` section::

    [metoffice]
    site id = 12345678
    aws pin = 987654
    template = default

    [logged]
    services = ['metoffice', 'underground']

Open Weather Map
^^^^^^^^^^^^^^^^

* Web site: http://openweathermap.org/
* Create account: http://home.openweathermap.org/users/sign_up
* API: http://openweathermap.org/stations#trans
* Example ``weather.ini`` section::

    [openweathermap]
    lat = 51.501
    long = -0.142
    alt = 10
    user = ElizabethWindsor
    password = corgi
    id = Buck House
    template = default

    [logged]
    services = ['openweathermap', 'underground']

When choosing a user name you should avoid spaces (and probably non-ascii characters as well).
Having a space in your user name causes strange "internal server error" responses from the server.

The default behaviour is to use your user name to identify the weather station.
However, it's possible for a user to have more than one weather station, so there is an optional ``name`` parameter in the API that can be used to identify the station.
This appears as ``id`` in ``weather.ini``.
Make sure you choose a name that is not already in use.

PWS Weather
^^^^^^^^^^^

* Web site: http://www.pwsweather.com/
* Create account: http://www.pwsweather.com/register.php
* API based on WU protocol: `<http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol>`_
* Example ``weather.ini`` section::

    [pwsweather]
    station = ABCDEFGH1
    password = xxxxxxx
    template = default

    [logged]
    services = ['pwsweather', 'underground']

temperatur.nu
^^^^^^^^^^^^^

* Web site: http://www.temperatur.nu/
* Example ``weather.ini`` section::

    [temperaturnu]
    hash = ???
    template = default

    [logged]
    services = ['temperaturnu', 'underground']

You receive the hash value from the temperatur.nu admins during sign
up.  It looks like "d3b07384d113edec49eaa6238ad5ff00".

Weather Underground
^^^^^^^^^^^^^^^^^^^

* Create account: http://www.wunderground.com/members/signup.asp
* API: `<http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol>`_
* Example ``weather.ini`` section::

    [underground]
    station = ABCDEFGH1
    password = xxxxxxx
    template = default

    [logged]
    services = ['underground', 'metoffice']

Weather Underground "RapidFire" updates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Weather Underground has a second upload URL for real time updates as little as 2.5 seconds apart.
If you run pywws in 'live logging' mode (see :doc:`livelogging`) you can use this to send updates every 48 seconds, by adding 'underground_rf' to the ``[live]`` tasks section in ``weather.ini``::

 [underground]
 station = ABCDEFGH1
 password = xxxxxxx
 template = default

 [live]
 services = ['underground_rf']

 [logged]
 services = ['underground', 'metoffice']

Make sure you still have an 'underground' service in ``[logged]`` or ``[hourly]``.
This will ensure that 'catchup' records are sent to fill in any gaps if your station goes offline for some reason.

wetter.com
^^^^^^^^^^

* Web site: http://www.wetter.com/wetter_aktuell/wetternetzwerk/
* Register station: http://www.wetter.com/mein_wetter/wetterstation/willkommen/
* Example ``weather.ini`` section::

    [wetterarchivde]
    user_id = 12345
    kennwort = ab1d3456i8
    template = default

    [logged]
    services = ['wetterarchivde', 'underground']

    [live]
    services = ['wetterarchivde', 'underground_rf']

Custom Request Headers
----------------------

The :py:mod:`pywws.toservice` module does support the injection of one or more
custom request headers for special cases where you want to integrate with a
service that, for example, requires you to pass an authentication key header
along with each request, such as ``x-api-key``.

These headers can be added to your ``a_service.ini`` file in the format of key
value pairs::

    [config]
    url		= https://my-aws-api-gw.execute-api.eu-west-1.amazonaws.com/test/station
    catchup		= 100
    interval	= 0
    use get		= True
    result		= []
    auth_type	= None
    http_headers	= [('x-api-key', 'my-api-key'), ('x-some-header', 'value')]
