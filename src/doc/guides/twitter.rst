.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-17  pywws contributors

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

How to configure pywws to post messages to Twitter
==================================================

Install dependencies
--------------------

Posting to Twitter requires some extra software.
See :doc:`../essentials/dependencies` - :ref:`dependencies-twitter`.

Create a Twitter account
------------------------

You could post weather updates to your 'normal' Twitter account, but I think it's better to have a separate account just for weather reports.
This could be useful to someone who lives in your area, but doesn't want to know what you had for breakfast.

Authorise pywws to post to your Twitter account
-----------------------------------------------

If you run pywws on a low power device such as a router, you may find it easier to run this authorisation step on another computer, as long as it has ``python-oauth2`` installed.
Use an empty 'data' directory -- a ``weather.ini`` file will be created whose contents can be copied into your real ``weather.ini`` file using any text editor.

Make sure no other pywws software is running, then run :py:mod:`~pywws.TwitterAuth`::

   python -m pywws.TwitterAuth ~/weather/data

(Replace ``~/weather/data`` with your data directory.)

This will open a web browser window (or give you a URL to copy to your web browser) where you can log in to your Twitter account and authorise pywws to post.
Your web browser will then show a 7 digit number which you need to copy to the :py:mod:`~pywws.TwitterAuth` program.
If successful, your ``weather.ini`` file will now have a ``[twitter]`` section with ``secret`` and ``key`` entries.
(Don't disclose these to anyone else.)

Add location data (optional)
----------------------------

Edit your ``weather.ini`` file and add ``latitude`` and ``longitude`` entries to the ``[twitter]`` section.
For example::

   [twitter]
   secret = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   key = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   latitude = 51.501
   longitude = -0.142

Create a template
-----------------

Twitter messages are generated using a template, just like creating files to upload to a website.
Copy the example template 'tweet.txt' to your template directory, then test it::

   python -m pywws.Template ~/weather/data ~/weather/templates/tweet.txt tweet.txt
   cat tweet.txt

(Replace ``~/weather/data`` and ``~/weather/templates`` with your data and template directories.)
If you need to change the template (e.g. to change the units or language used) you can edit it now or later.

Post your first weather Tweet
-----------------------------

Now everything is prepared for :py:mod:`~pywws.ToTwitter` to be run::

   python -m pywws.ToTwitter ~/weather/data tweet.txt

If this works, your new Twitter account will have posted its first weather report.
(You should delete the tweet.txt file now.)

Add Twitter updates to your hourly tasks
----------------------------------------

Edit your ``weather.ini`` file and edit the ``[hourly]`` section.
For example::

   [hourly]
   services = []
   plot = ['7days.png.xml', '24hrs.png.xml', 'rose_12hrs.png.xml']
   text = [('tweet.txt', 'T'), '24hrs.txt', '6hrs.txt', '7days.txt']

Note the use of the ``'T'`` flag -- this tells pywws to tweet the template result instead of uploading it to your ftp site.

You could change the ``[logged]``, ``[12 hourly]`` or ``[daily]`` sections instead, but I think ``[hourly]`` is most appropriate for Twitter updates.

.. versionchanged:: 13.06_r1015
   added the ``'T'`` flag.
   Previously Twitter templates were listed separately in ``twitter`` entries in the ``[hourly]`` and other sections.
   The older syntax still works, but is deprecated.

Include an image in your tweet
------------------------------

.. versionadded:: 14.05.dev1216

You can add up to four images to your tweets by specifying the image file locations in the tweet template.
Make the first line of the tweet ``media path`` where ``path`` is the absolute location of the file.
Repeat for any additional image files.
The "tweet_media.txt" example template shows how to do this.

The image could be from a web cam, or for a weather forecast it could be an icon representing the forecast.
To add a weather graph you need to make sure the graph is drawn before the tweet is sent.
I do this by using two ``[cron xxx]`` sections in weather.ini::

   [cron prehourly]
   format = 59 * * * *
   services = []
   plot = [('tweet.png.xml', 'L')]
   text = []

   [cron hourly]
   format = 0 * * * *
   services = []
   plot = ['7days.png.xml', '24hrs.png.xml', 'rose_12hrs.png.xml']
   text = [('tweet_media.txt', 'T'), '24hrs.txt', '6hrs.txt', '7days.txt']
