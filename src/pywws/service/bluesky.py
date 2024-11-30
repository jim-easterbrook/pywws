# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-24  pywws contributors

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Post messages to Bluesky.

Bluesky is a micro-blogging system that is a whole lot better than the
cesspool Twitter has become under Space Karen. This module
sends "skeets", with optional image files, typically to report on weather
conditions every hour.


* Create account: https://bsky.app/
* Example ``weather.ini`` configuration::

    [bluesky]
    handle = bishopstonwthr.bsky.social
    password = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    [hourly]
    text = ['skeet.txt', '24hrs.txt']
    plot = ['24hrs.png.xml', 'rose_12hrs.png.xml']
    services = [('bluesky', 'skeet.txt'), ('ftp', '24hrs.png', 'rose_12hrs.png')]

Create an account
-----------------

You could post weather updates to your regular Bluesky but it may be 
cleaner to have a separate account just for weather reports.

The :py:mod:`pywws.service.bluesky` module requires you to install an
additional dependency::

    sudo pip install atprototools

Authorise pywws
---------------

Before you can send "skeets" you need to authorise pywws to post to your
account. If you run pywws on a low power device such as a Raspberry Pi,
you may find it easier to generate an app password on a browser on
another computer and type the values into the ``weather.ini`` file using
any text editor.

Log into your Bluesky account in a browser and navigate to Settings ->
Privacy and security -> App Passwords -> Add App Password. Give it a 
memorable name (or use a randomly generated one) and then make a note of
the password in the next section; it won't be displayed again. This 
password will give access to your account, and should be kept
confidential.

Create a template
-----------------

A "skeet" is a short text of up to 300 characters. It's up to you what to
put in your "skeet" but an example is included to get your started. Copy
the example template ``skeet.txt`` to your template directory, then edit
it to suit your preferences. (Note hashtags are not automatically
rendered as hash tags, and getting them to work is complicated as you
have to figure out the start/end position in the post text, that's just
too hard for this currently). You should also check it uses the same text
encoding as your other templates. The example template includes a
``media`` line to send a graph. Either remove this or copy the example
graph template ``tweet.png.xml`` to your graph templates directory, if
you don't already have one there.

Now generate a skeet file from your template, for example::

    python -m pywws.template ~/weather/data ~/weather/templates/skeet.txt skeet.txt
    cat skeet.txt

Post your first skeet
--------------------

Now you are ready to run :py:mod:`pywws.service.bluesky`::

    python -m pywws.service.bluesky ~/weather/data skeet.txt

If this works, your new Bluesky account will have posted its first
weather report. (You can delete the skeet.txt file now.)

Add Bluesky posts to your hourly tasks
---------------------------------------

Edit the ``[hourly]`` section in ``weather.ini``. If your skeets include
one or more graphs you need to add the graph templates to the ``plot``
list. Note that if you reuse your Twitter graph you only need to
generate it once. Add your skeet template to the ``text`` list. Finally,
add ``bluesky`` to the ``services`` list, with an option specifying the
template processing result. For example::

    [hourly]
    text = ['skeet.txt']
    plot = ['tweet.png.xml']
    services = [('bluesky', 'skeet.txt')]

You could use the ``[logged]``, ``[12 hourly]`` or ``[daily]`` sections
instead, but I think ``[hourly]`` is most appropriate for Bluesky
updates.

Include images in your skeet
----------------------------

Each post contains up to four images, and each image can have its own
alt text and is limited to 1,000,000 bytes in size. However, the
atprototools libary used to interface with Bluesky is currently coded
to just manage a single image; it also cannot accept ALT text for the
image.

To include an image ensure the first line of the skeet is ``media path``
where ``path`` is the file name or full path for file
that are not in your "output" directory (a subdirectory of your work
directory called ``output``). . The "skeet_media.txt" example template
shows how to do this.

The image could be from a web cam, or for a weather forecast it could be
an icon representing the forecast. To add a weather graph you need to
make sure the graph is drawn before the tweet is sent. The
:py:mod:`pywws.regulartasks` module processes graph and text templates
before doing service uploads, so you can include the graph drawing in
the same section. For example::

    [hourly]
    plot = ['skeet.png.xml']
    text = ['skeet_media.txt']
    services = [('bluesky', 'skeet_media.txt')]

.. _Bluesky: https://bsky.app/

"""

from __future__ import absolute_import, print_function

import codecs
from contextlib import contextmanager
import logging
import os
import sys

import atprototools

import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)

class ToService(pywws.service.FileService):
    config = {
        'handle'      : (None, True, None),
        'password'    : (None, True, None),
        }
    logger = logger
    service_name = service_name

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        # get default character encoding of template output
        self.encoding = context.params.get(
            'config', 'template encoding', 'iso-8859-1')

    @contextmanager
    def session(self):
        yield atprototools.Session(self.params['handle'], self.params['password'])

    def upload_file(self, session, filename):
        media=None
        with codecs.open(filename, 'r', encoding=None) as skeet_file:
            skeet = skeet_file.read()
        while skeet.startswith('media'):
            media_item, skeet = skeet.split('\n', 1)
            media_item = media_item.split()[1]
            if not os.path.isabs(media_item):
                media = os.path.join(self.context.output_dir, media_item)
        try:
            session.postBloot(skeet,image_path=media)
        except Exception as ex:
            return False, repr(ex)
        return True, 'OK'

    def register(self):
        self.check_params('handle', 'password')
        #not sure what else to put here, or how to get an app password programmatically

if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
