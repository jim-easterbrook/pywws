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

How to integrate pywws with various weather services
====================================================

This guide gives brief instructions on how to use pywws with some other weather services and software.
It is not comprehensive, and most services (such as Twitter) are covered in more detail elsewhere.

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

The remaining weather service uploads are handled by modules in the :ref:`pywws.service <api-index-services>` sub-package.

.. autosummary::

   pywws.service.cwop
   pywws.service.metoffice
   pywws.service.mqtt
   pywws.service.openweathermap
   pywws.service.pwsweather
   pywws.service.temperaturnu
   pywws.service.underground
   pywws.service.wetterarchivde

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
#. Restart pywws live logging.

Many of the services will upload the last seven days of data (referred to as "catchup" mode) when first run.
This may take an hour or more, but the use of separate threads means this doesn't adversely affect the rest of pywws.
