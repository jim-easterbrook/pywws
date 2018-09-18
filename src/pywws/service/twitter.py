# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-18  pywws contributors

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

"""Post messages to Twitter.

Twitter_ is a popular micro-blogging service. Users send short messages
(up to 280 characters) called "tweets". This module sends tweets, with
optional image files, typically to report on weather conditions every
hour.

* Create account: https://twitter.com/
* Additional dependencies:

  * https://github.com/joestump/python-oauth2
  * https://github.com/bear/python-twitter *or*
    https://github.com/tweepy/tweepy
* Example ``weather.ini`` configuration::

    [twitter]
    secret = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    key = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    latitude = 51.501
    longitude = -0.142

    [hourly]
    plot = ['tweet.png.xml', '24hrs.png.xml', 'rose_12hrs.png.xml']
    text = ['tweet_media.txt', '24hrs.txt']
    services = [('twitter', 'tweet_media.txt'),
                ('ftp', '24hrs.png', 'rose_12hrs.png', '24hrs.txt')]

Create an account
-----------------

You could post weather updates to your ‘normal’ Twitter account, but I
think it’s better to have a separate account just for weather reports.
This could be useful to someone who lives in your area, but doesn’t want
to know what you had for breakfast.

The :py:mod:`pywws.service.twitter` module requires you to install
additional dependencies. There is a choice of Python Twitter library.
Use either ``python-twitter`` (preferred) or ``tweepy``::

    sudo pip install python-twitter oauth2

*or* ::

    sudo pip install tweepy oauth2

Authorise pywws
---------------

Before you can send tweets you need to authorise pywws to post to your
account. If you run pywws on a low power device such as a Raspberry Pi,
you may find it easier to run this authorisation step on another
computer, as long as it has the required dependencies installed. You can
use an empty 'data' directory -- a ``weather.ini`` file will be created
whose contents can be copied into your real ``weather.ini`` file using
any text editor.

Make sure no other pywws software is running, then run the module with
the ``-r`` option. (Remember to replace ``data_dir`` with your data
directory.) ::

    python -m pywws.service.twitter -r data_dir

This will open a web browser window (or give you a URL to copy to your
web browser) where you can log in to your Twitter account and authorise
pywws to post. If the login is successful the browser will display a 7
digit number which you then copy to pywws::

    jim@brains:~$ python3 -m pywws.service.twitter -r weather_data
    14:19:21:pywws.logger:pywws version 18.8.0, build 1566 (5054dc7)
    Please enter the PIN shown in your web browser: 2594624
    jim@brains:~$ 

The ``secret`` and ``key`` values stored in ``weather.ini`` give access
to your Twitter account and should be kept confidential.

Add location data (optional)
----------------------------

Edit your ``weather.ini`` file and add ``latitude`` and ``longitude``
entries to the ``[twitter]`` section. For example::

   [twitter]
   secret = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   key = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   latitude = 51.501
   longitude = -0.142

Create a template
-----------------

A tweet is a short text of up to 280 characters (fewer if you include
images). It's up to you what to put in your tweets but an example is
included to get your started. Copy the example template ``tweet.txt`` to
your template directory, then edit it to suit your preferences. You
should also check it uses the same text encoding as your other
templates.

Now generate a tweet file from your template, for example::

    python -m pywws.template ~/weather/data ~/weather/templates/tweet.txt tweet.txt
    cat tweet.txt

(Replace ``~/weather/data`` and ``~/weather/templates`` with your data
and template directories.) If you need to change the template (e.g. to
change the units or language used) you can edit it now or later.

Post your first tweet
---------------------

Now you are ready to run :py:mod:`pywws.service.twitter`. Using high
verbosity shows you what's happening as it runs::

    python -m pywws.service.twitter -vv ~/weather/data tweet.txt

If this works, your new Twitter account will have posted its first
weather report. (You can delete the tweet.txt file now.)

Add Twitter posts to your hourly tasks
--------------------------------------

Edit the ``[hourly]`` section in ``weather.ini``. Add your tweet
template to the ``text`` list. Then add ``twitter`` to the ``services``
list, with an option specifying the template processing result. For
example::

    [hourly]
    text = ['tweet.txt']
    services = [('twitter', 'tweet.txt')]

You could use the ``[logged]``, ``[12 hourly]`` or ``[daily]`` sections
instead, but I think ``[hourly]`` is most appropriate for Twitter
updates.

Include images in your tweet
----------------------------

You can add up to four images to your tweets by specifying the image
file locations in the tweet template. Make the first line of the tweet
``media path`` where ``path`` is the file name, or full path for files
that are not in your "output" directory (a subdirectory of your work
directory called ``output``). Repeat for any additional image files. The
"tweet_media.txt" example template shows how to do this.

The image could be from a web cam, or for a weather forecast it could be
an icon representing the forecast. To add a weather graph you need to
make sure the graph is drawn before the tweet is sent. The
:py:mod:`pywws.regulartasks` module processes graph and text templates
before doing service uploads, so you can include the graph drawing in
the same section. For example::

    [hourly]
    plot = ['tweet.png.xml']
    text = ['tweet_media.txt']
    services = [('twitter', 'tweet_media.txt')]

.. _Twitter: https://twitter.com/

"""

from __future__ import absolute_import, print_function

import codecs
from contextlib import contextmanager
import logging
import os
import sys

twitter = None
tweepy = None
try:
    import twitter
except ImportError as ex:
    try:
        import tweepy
    except ImportError:
        # raise exception on the preferred library
        raise ex

from pywws.constants import Twitter as pct
import pywws.service

__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)


class TweepyHandler(object):
    def __init__(self, key, secret, latitude, longitude):
        logger.info('Using tweepy library')
        auth = tweepy.OAuthHandler(pct.consumer_key, pct.consumer_secret)
        auth.set_access_token(key, secret)
        self.api = tweepy.API(auth)
        if latitude is not None and longitude is not None:
            self.kwargs = {'lat' : latitude, 'long' : longitude}
        else:
            self.kwargs = {}

    def post(self, status, media):
        if len(media) > 1:
            logger.error('Tweepy library cannot post multiple media')
        if media:
            self.api.update_with_media(media[0], status[:257], **self.kwargs)
        else:
            self.api.update_status(status[:280], **self.kwargs)


class PythonTwitterHandler(object):
    def __init__(self, key, secret, latitude, longitude, timeout):
        logger.info('Using python-twitter library')
        self.api = twitter.Api(
            consumer_key=pct.consumer_key,
            consumer_secret=pct.consumer_secret,
            access_token_key=key, access_token_secret=secret,
            timeout=timeout)
        if latitude is not None and longitude is not None:
            self.kwargs = {'latitude' : latitude, 'longitude' : longitude,
                           'display_coordinates' : True}
        else:
            self.kwargs = {}
        self.kwargs['verify_status_length'] = False


    def post(self, status, media):
        max_len = 280
        if media:
            max_len -= len(media[:4]) * 23
        status = status.strip()[:max_len]
        args = dict(self.kwargs)
        if media:
            args['media'] = media
        self.api.PostUpdate(status, **args)


class ToService(pywws.service.FileService):
    config = {
        'secret'   : (None, True,  None),
        'key'      : (None, True,  None),
        'latitude' : (None, False, None),
        'longitude': (None, False, None),
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
        if twitter:
            yield PythonTwitterHandler(
                self.params['key'], self.params['secret'],
                self.params['latitude'], self.params['longitude'], 40)
        else:
            yield TweepyHandler(
                self.params['key'], self.params['secret'],
                self.params['latitude'], self.params['longitude'])

    def upload_file(self, session, filename):
        with codecs.open(filename, 'r', encoding=self.encoding) as tweet_file:
            tweet = tweet_file.read()
        media = []
        while tweet.startswith('media'):
            media_item, tweet = tweet.split('\n', 1)
            media_item = media_item.split()[1]
            if not os.path.isabs(media_item):
                media_item = os.path.join(self.context.output_dir, media_item)
            media.append(media_item)
        try:
            session.post(tweet, media)
        except Exception as ex:
            message = repr(ex)
            return 'is a duplicate' in message, message
        return True, 'OK'

    def register(self):
        import webbrowser
        if sys.version_info[0] >= 3:
            from urllib.parse import parse_qsl
        else:
            from urlparse import parse_qsl
        import oauth2 as oauth

        consumer = oauth.Consumer(pct.consumer_key, pct.consumer_secret)
        client = oauth.Client(consumer)
        # step 1 - obtain a request token
        resp, content = client.request(
            'https://api.twitter.com/oauth/request_token', 'POST')
        if resp['status'] != '200':
            print('Failed to get request token. [%s]' % resp['status'])
            return
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        request_token = dict(parse_qsl(content))
        # step 2 - redirect the user
        redirect_url = 'https://api.twitter.com/oauth/authorize?oauth_token=%s' % (
            request_token['oauth_token'])
        if not webbrowser.open(redirect_url, new=2, autoraise=0):
            print('Please use a web browser to open the following URL')
            print(redirect_url)
        if sys.version_info[0] >= 3:
            input_ = input
        else:
            input_ = raw_input
        pin = input_('Please enter the PIN shown in your web browser: ')
        pin = pin.strip()
        # step 3 - convert the request token to an access token
        token = oauth.Token(
            request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(pin)
        client = oauth.Client(consumer, token)
        resp, content = client.request(
            'https://api.twitter.com/oauth/access_token', 'POST')
        if resp['status'] != '200':
            print('Failed to get access token. [%s]' % resp['status'])
            return
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        access_token = dict(parse_qsl(content))
        self.context.params.set(
            service_name, 'key', access_token['oauth_token'])
        self.context.params.set(
            service_name, 'secret', access_token['oauth_token_secret'])


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))
