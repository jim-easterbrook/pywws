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

Weather Underground
-------------------

`Weather Underground <http://www.wunderground.com/>`_ (or Wunderground) is one of the longest established weather websites in the world.
Like many other such services, pywws can send weather data to it over the internet.
The :py:mod:`pywws.toservice` module handles this communication for a range of online services.

The first step is to set up a Weather Underground account at `<http://www.wunderground.com/members/signup.asp>`_.
Then use the "Add A Station" form to provide details of your station such as its location and type.
You should then get a station ID and password -- make a note of these.

Now stop any pywws software that's running, then try using :py:mod:`pywws.toservice` directly::

 python -m pywws.toservice ~/weather/data underground

This should fail, as you haven't set the station ID or password yet, but it creates entries in ``weather.ini`` for you to edit.
Edit ``weather.ini`` and find the ``[underground]`` section::

 [underground]
 station = unknown
 password = unknown

Replace the ``unknown`` values with your station ID and password.

Now try :py:mod:`pywws.toservice` again::

 python -m pywws.toservice ~/weather/data underground

If this worked then you can upload your last 7 days worth of data.
Note that this might take quite a long time, especially if you have a short 'logging interval'.
First edit ``status.ini`` and remove the ``underground`` entry from the ``[last update]`` section.
Then run :py:mod:`pywws.toservice` with the 'catchup' option, and high verbosity so you can see it working::

 python -m pywws.toservice -vvc ~/weather/data underground

Once everything is working, you can add 'underground' to the ``[logged]`` tasks section in ``weather.ini``::

 [logged]
 services = ['underground']

"RapidFire" updates
^^^^^^^^^^^^^^^^^^^
Weather Underground has a second upload URL for real time updates as little as 2.5 seconds apart.
If you run pywws in 'live logging' mode (see :doc:`livelogging`) you can use this to send updates every 48 seconds, by adding 'underground_rf' to the ``[live]`` tasks section in ``weather.ini``::

 [live]
 services = ['underground_rf']

It is not clear if Weather Underground approves of sending both RapidFire and normal updates for the same station.
(See `<http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol#RapidFire_Updates>`_.)
If you only use RapidFire there is a possibility of gaps in the history if your station goes "off air" for some reason.

Comments or questions? Please subscribe to the pywws mailing list http://groups.google.com/group/pywws and let us know.