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

"""Post a message to Twitter.

Before posting to Twitter you need to authorise pywws by running the
module with the ``-r`` option.

If you run pywws on a low power device such as a Raspberry Pi, you may
find it easier to run this authorisation step on another computer, as
long as it has the required dependencies installed. You can use an empty
'data' directory -- a ``weather.ini`` file will be created whose
contents can be copied into your real ``weather.ini`` file using any
text editor.

Make sure no other pywws software is running, then run the module with
the ``-r`` option::

    python -m pywws.totwitter -r data_dir

(Replace ``data_dir`` with your data directory.)

This will open a web browser window (or give you a URL to copy to your
web browser) where you can log in to your Twitter account and authorise
pywws to post. If the login is successful the browser will display a 7
digit number which you then copy to pywws::

    jim@brains:~/Documents/projects/pywws/master$ python -m pywws.totwitter -r ../data/ 
    12:20:08:pywws.logger:pywws version 18.4.2, build 1521 (487c307)
    Please enter the PIN shown in your web browser: 9069882
    Success! Authorisation data has been stored in ../data/weather.ini
    jim@brains:~/Documents/projects/pywws/master$

The ``secret`` and ``key`` values stored in ``weather.ini`` give access
to your Twitter account and should be kept confidential.

.. _Twitter: https://twitter.com/

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"

import codecs
from contextlib import contextmanager
from datetime import timedelta
import logging
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
import pywws.localisation
import pywws.logger
import pywws.service
import pywws.storage

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


class ToTwitter(object):
    catchup = -1
    interval = timedelta(seconds=150)
    logger = logger
    log_count = True
    service_name = 'pywws.totwitter'

    def __init__(self, context):
        self.params = context.params
        # get parameters
        key = context.params.get('twitter', 'key')
        secret = context.params.get('twitter', 'secret')
        if (not key) or (not secret):
            raise RuntimeError('Authentication data not found')
        latitude = context.params.get('twitter', 'latitude')
        longitude = context.params.get('twitter', 'longitude')
        # open API
        if twitter:
            self.api = PythonTwitterHandler(
                key, secret, latitude, longitude, 40)
        else:
            self.api = TweepyHandler(key, secret, latitude, longitude)
        # create upload thread
        self.upload_thread = pywws.service.UploadThread(self, context)
        self.stop = self.upload_thread.stop

    @contextmanager
    def session(self):
        yield None

    def upload_data(self, session, tweet=''):
        media = []
        while tweet.startswith('media'):
            media_item, tweet = tweet.split('\n', 1)
            media_item = media_item.split()[1]
            media.append(media_item)
        try:
            self.api.post(tweet, media)
        except Exception as ex:
            message = str(ex)
            return 'is a duplicate' in message, message
        return True, 'OK'

    def upload(self, tweet):
        if not tweet:
            return
        self.upload_thread.queue.append((None, {'tweet': tweet}))
        # start upload thread
        if not self.upload_thread.is_alive():
            self.upload_thread.start()

    def upload_file(self, file):
        # get default character encoding of template output
        encoding = self.params.get('config', 'template encoding', 'iso-8859-1')
        with codecs.open(file, 'r', encoding=encoding) as tweet_file:
            tweet = tweet_file.read()
        return self.upload(tweet)


def twitter_auth(params):
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
        return 1
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
        return 1
    if isinstance(content, bytes):
        content = content.decode('utf-8')
    access_token = dict(parse_qsl(content))
    params.set('twitter', 'key', access_token['oauth_token'])
    params.set('twitter', 'secret', access_token['oauth_token_secret'])
    print('Success! Authorisation data has been stored in %s' % params._path)
    return 0


def main(argv=None):
    import argparse
    import inspect
    if argv is None:
        argv = sys.argv
    docstring = inspect.getdoc(sys.modules[__name__]).split('\n\n')
    parser = argparse.ArgumentParser(
        description=docstring[0], epilog=docstring[1])
    parser.add_argument('-r', '--register', action='store_true',
                        help='authorise pywws to post to your account')
    parser.add_argument('-v', '--verbose', action='count',
                        help='increase amount of reassuring messages')
    parser.add_argument('data_dir', help='root directory of the weather data')
    parser.add_argument('file', nargs='*', help='file to be uploaded')
    args = parser.parse_args(argv[1:])
    pywws.logger.setup_handler(args.verbose or 0)
    with pywws.storage.pywws_context(args.data_dir) as context:
        if args.register:
            twitter_auth(context.params)
            context.flush()
            return 0
        uploader = ToTwitter(context)
        for file in args.file:
            uploader.upload_file(file)
        uploader.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
