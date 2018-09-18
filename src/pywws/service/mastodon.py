# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2018  pywws contributors

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

"""Post messages to Mastodon.

Mastodon_ is a micro-blogging system that at first sight looks a bit
like Twitter. In many ways it's quite different though. This module
sends "toots", with optional image files, typically to report on weather
conditions every hour.

* Create account: https://joinmastodon.org/
* Additional dependency: https://mastodonpy.readthedocs.io/
* Example ``weather.ini`` configuration::

    [mastodon]
    handle = kt19weather@botsin.space
    client_id = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    client_secret = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    access_token = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    [hourly]
    text = ['toot.txt', 'tweet_media.txt', '24hrs.txt']
    plot = ['tweet.png.xml', '24hrs.png.xml', 'rose_12hrs.png.xml']
    services = [('mastodon', 'toot.txt'), ('twitter', 'tweet_media.txt'),
                ('ftp', '24hrs.png', 'rose_12hrs.png', '24hrs.txt')]

Create an account
-----------------

Before creating a Mastodon account for your weather reports you need to
choose an "instance". Mastodon is a federated system, running on many
interconnected servers, each of which is called an instance. Choose one
whose rules allow "bots" (i.e. automated posts) such as `botsin.space`_.
After creating an account, edit its profile and make sure the "this is a
bot account" box is selected.

The :py:mod:`pywws.service.mastodon` module requires you to install an
additional dependency::

    sudo pip install mastodon.py

Authorise pywws
---------------

Before you can send "toots" you need to authorise pywws to post to your
account. If you run pywws on a low power device such as a Raspberry Pi,
you may find it easier to run this authorisation step on another
computer, as long as it has the required dependencies installed. You can
use an empty 'data' directory -- a ``weather.ini`` file will be created
whose contents can be copied into your real ``weather.ini`` file using
any text editor.

Make sure no other pywws software is running, then run the module with
the ``-r`` option. (Remember to replace ``data_dir`` with your data
directory.) ::

    python -m pywws.service.mastodon -r data_dir

The first time you do this it will probably crash because you haven't
set your Mastodon "handle" in ``weather.ini``. Edit ``weather.ini`` and
add your handle as shown above, then run the module with the ``-r``
option again.

This will open a web browser window (or give you a URL to copy to your
web browser) where you can log in to your Mastodon account and authorise
pywws to post. If the login is successful the browser will display a
long code string which you then copy to pywws::

    jim@brains:~$ python3 -m pywws.service.mastodon -r weather_data
    07:45:34:pywws.logger:pywws version 18.8.0, build 1564 (5bfc528)
    Please enter the auth code shown in your web browser: 12573ba24341b5de2a1f2930fc93889c3576af7b50ecd9d713fa502d773805b4
    jim@brains:~$ 

The ``access_token`` value stored in ``weather.ini`` gives access to
your Mastodon account and should be kept confidential.

Create a template
-----------------

A "toot" is a short text of up to 500 characters. It's up to you what to
put in your "toots" but an example is included to get your started. Copy
the example template ``toot.txt`` to your template directory, then edit
it to suit your preferences. (At least change the hashtags to suit your
location.) You should also check it uses the same text encoding as your
other templates. The example template includes a ``media`` line to send
a graph. Either remove this or copy the example graph template
``tweet.png.xml`` to your graph templates directory, if you don't
already have one there.

Now generate a toot file from your template, for example::

    python -m pywws.template ~/weather/data ~/weather/templates/toot.txt toot.txt
    cat toot.txt

Post your first toot
--------------------

Now you are ready to run :py:mod:`pywws.service.mastodon`::

    python -m pywws.service.mastodon ~/weather/data toot.txt

If this works, your new Mastodon account will have posted its first
weather report. (You can delete the toot.txt file now.)

Add Mastodon posts to your hourly tasks
---------------------------------------

Edit the ``[hourly]`` section in ``weather.ini``. If your toots include
one or more graphs you need to add the graph templates to the ``plot``
list. Note that if you reuse your Twitter graph you only need to
generate it once. Add your toot template to the ``text`` list. Finally,
add ``mastodon`` to the ``services`` list, with an option specifying the
template processing result. For example::

    [hourly]
    text = ['toot.txt']
    plot = ['tweet.png.xml']
    services = [('mastodon', 'toot.txt')]

You could use the ``[logged]``, ``[12 hourly]`` or ``[daily]`` sections
instead, but I think ``[hourly]`` is most appropriate for Mastodon
updates.

Add more images
---------------

Mastodon allows up to four images per "toot", so you could add more
graphs, or a webcam image, or a weather forecast icon. Use one ``media``
line per image at the start of your toot template. You need to give the
full path of any files that are not in your "output" directory (a
subdirectory of your work directory called ``output``).

.. _botsin.space: https://botsin.space/
.. _Mastodon: https://joinmastodon.org/

"""

from __future__ import absolute_import, print_function

import codecs
from contextlib import contextmanager
import logging
import os
import sys

from mastodon import Mastodon

import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class ToService(pywws.service.FileService):
    config = {
        'handle'      : ('',   True, None),
        'access_token': (None, True, None),
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
        yield Mastodon(access_token=self.params['access_token'],
                       api_base_url=self.params['handle'].split('@')[-1])

    def upload_file(self, session, filename):
        with codecs.open(filename, 'r', encoding=self.encoding) as toot_file:
            toot = toot_file.read()
        media = []
        while toot.startswith('media'):
            media_item, toot = toot.split('\n', 1)
            media_item = media_item.split()[1]
            if not os.path.isabs(media_item):
                media_item = os.path.join(self.context.output_dir, media_item)
            media.append(media_item)
        media_ids = []
        try:
            for media_item in media:
                rsp = session.media_post(media_item)
                media_ids.append(rsp['id'])
            rsp = session.status_post(status=toot, media_ids=media_ids)
        except Exception as ex:
            return False, repr(ex)
        return True, 'OK'

    def register(self):
        import webbrowser

        self.check_params('handle')
        api_base_url = self.params['handle'].split('@')[-1]
        # get client data
        client_id = self.context.params.get(service_name, 'client_id')
        client_secret = self.context.params.get(service_name, 'client_secret')
        if (not client_id) or (not client_secret):
            client_id, client_secret = Mastodon.create_app(
                'pywws', scopes=['write'], api_base_url=api_base_url)
            self.context.params.set(service_name, 'client_id', client_id)
            self.context.params.set(service_name, 'client_secret', client_secret)
        # create api
        api = Mastodon(client_id=client_id, client_secret=client_secret,
                       api_base_url=api_base_url)
        # authorise
        auth_request_url = api.auth_request_url(scopes=['write'])
        if not webbrowser.open(auth_request_url, new=2, autoraise=0):
            print('Please use a web browser to open the following URL')
            print(auth_request_url)
        if sys.version_info[0] >= 3:
            input_ = input
        else:
            input_ = raw_input
        code = input_('Please enter the auth code shown in your web browser: ')
        code = code.strip()
        # log in
        access_token = api.log_in(code=code, scopes=['write'])
        self.context.params.set(service_name, 'access_token', access_token)


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
