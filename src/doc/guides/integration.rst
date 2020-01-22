.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-20  pywws contributors

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
It is not comprehensive, and most services are covered in more detail elsewhere.

YoWindow
--------

`YoWindow <http://yowindow.com/>`_ is a weather display widget that can display data from an internet source, or from your weather station.
To display data from your station pywws needs to write to a local file, typically every 48 seconds when new data is received.
This is easy to do:

#. Stop all pywws software
#. Copy the ``yowindow.xml`` example template to your text template directory.
#. Add the yowindow template to the ``[live]`` tasks in ``weather.ini``::

     [live]
     text = ['yowindow.xml']
#. Restart pywws live logging.

This will write the file to the ``output`` subdirectory of the ``work`` directory set in :ref:`weather.ini <weather_ini-paths>`.
If you prefer to store the file somewhere else you can use the :py:mod:`pywws.service.copy` service to copy it there. For example::

    [copy]
    directory = /home/heavyweather/

    [live]
    text = ['yowindow.xml']
    services = [('copy', 'yowindow.xml')]

You can check the file is being updated every 48 seconds by using ``more`` or ``cat`` to dump it to the screen.

Finally configure yowindow to use this file.
See `<http://yowindow.com/pws_setup.php>`_ for instructions on how to do this.

.. _guides-integration-other:

Other "services"
----------------

The remaining weather service uploads are handled by modules in the :ref:`pywws.service <api-index-services>` sub-package.

.. autosummary::

   pywws.service.ftp
   pywws.service.sftp
   pywws.service.copy
   pywws.service.cwop
   pywws.service.metoffice
   pywws.service.mqtt
   pywws.service.openweathermap
   pywws.service.pwsweather
   pywws.service.temperaturnu
   pywws.service.underground
   pywws.service.weathercloud
   pywws.service.wetterarchivde
   pywws.service.windy
   pywws.service.twitter
   pywws.service.mastodon

These each use a separate thread to upload the data so that a slow or not responding service doesn't delay other processing or uploads.

The service uploaders are all used in a similar fashion:

#. Create an account with the service.
#. Stop all pywws software.
#. Run the service module directly to initialise its entry in ``weather.ini``. For example::

      python -m pywws.service.underground /home/jim/weather/data

#. Edit ``weather.ini`` and add your account details to the appropriate section (e.g. ``[underground]``).
#. Run the service module directly (with high verbosity) to make sure your account details are correct::

      python -m pywws.service.underground -vvv /home/jim/weather/data

   Each service's server software responds differently to correct or incorrect uploads.
   You should be able to tell from the response if it was successful or not.

#. Edit ``weather.ini`` and add the service to the ``[logged]`` (and optionally ``[live]``) sections, e.g.::

     [logged]
     services = ['underground']

     [live]
     services = ['underground']

   Note that some services, such as :py:mod:`pywws.service.copy`, need one or more parameters.
   Instead of a single word entry, such as ``underground``, these use a bracketed list, for example ``('copy', 'yowindow.xml')``.

#. Restart pywws live logging.

Some of the services are more complicated to configure.
More detailed instructions are given in the module's documentation.
Follow the links in the table above.

Many of the services will upload the last seven days of data (referred to as "catchup" mode) when first run.
This may take an hour or more, but the use of separate threads means this doesn't adversely affect the rest of pywws.

Writing your own uploader
-------------------------

If you'd like to send data to a service which is not (yet) included in pywws you can write your own uploader module and put it in your ``modules`` directory.
You should start by copying one of the existing modules from ``pywws.service``.
Choose one with an API most like the service you want to upload to.
Give the module a one word lowercase name that will be used as the uploader service name.

Testing the module is a little different from before::

   python ~/weather/modules/myservice.py -vvv ~/weather/data

where ``~/weather/modules/myservice.py`` is the full path of your new module.

Note what sort of response you get from the server.
Some servers, such as Weather Underground, send a single word ``'success'`` response to indicate success, and a longer string indicating the cause of any failure.
Other servers use HTTP response codes to indicate failure.
Your module's ``upload_data`` method must return a ``(bool, str)`` tuple where the ``bool`` value indicates success (if ``True``) and the ``str`` value contains any message from the server.
(If the server returns no message this string should be set to ``'OK'``.)
Under normal operation pywws will log this message whenever it changes.

Once your uploader is working you could contribute it to pywws if it's likely to be useful to other people.
Don't forget to document it fully, then either send it to Jim or create a GitHub pull request.
See :ref:`copyright-contributing` for instructions on doing this.
