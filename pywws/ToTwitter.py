#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-14  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

"""Post a message to Twitter
::

%s

This module posts a brief message to `Twitter
<https://twitter.com/>`_. Before posting to Twitter you need to set up
an account and then authorise pywws by running the
:py:mod:`TwitterAuth` program. See :doc:`../guides/twitter` for
detailed instructions.

"""

from __future__ import absolute_import

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.ToTwitter [options] data_dir file
 options are:
  -h | --help  display this help
 data_dir is the root directory of the weather data
 file is the text file to be uploaded
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import codecs
import getopt
import logging
import sys

twitter = None
tweepy = None
try:
    import twitter
except ImportError:
    import tweepy

from .constants import Twitter as pct
from . import DataStore
from . import Localisation
from .Logger import ApplicationLogger

class ToTwitter(object):
    def __init__(self, params):
        self.logger = logging.getLogger('pywws.ToTwitter')
        self.old_ex = None
        # get character encoding of template output
        self.encoding = params.get('config', 'template encoding', 'iso-8859-1')
        # get parameters
        key = params.get('twitter', 'key')
        secret = params.get('twitter', 'secret')
        if (not key) or (not secret):
            raise RuntimeError('Authentication data not found')
        latitude = params.get('twitter', 'latitude')
        longitude = params.get('twitter', 'longitude')
        # open API
        if twitter:
            self.api = twitter.Api(
                consumer_key=pct.consumer_key,
                consumer_secret=pct.consumer_secret,
                access_token_key=key, access_token_secret=secret)
            self.post = self.api.PostUpdate
            self.post_kw = {'latitude' : latitude, 'longitude' : longitude}
        else:
            auth = tweepy.OAuthHandler(pct.consumer_key, pct.consumer_secret)
            auth.set_access_token(key, secret)
            self.api = tweepy.API(auth)
            self.post = self.api.update_status
            self.post_kw = {'lat' : latitude, 'long' : longitude}

    def Upload(self, tweet):
        if not tweet:
            return True
        if not isinstance(tweet, unicode):
            tweet = tweet.decode(self.encoding)
        try:
            status = self.post(tweet, **self.post_kw)
            return True
        except Exception, ex:
            e = str(ex)
            if 'is a duplicate' in e:
                return True
            if e != self.old_ex:
                self.logger.error(e)
                self.old_ex = e
        return False

    def UploadFile(self, file):
        tweet_file = codecs.open(file, 'r', encoding=self.encoding)
        tweet = tweet_file.read(140)
        tweet_file.close()
        return self.Upload(tweet)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
            return 0
    # check arguments
    if len(args) != 2:
        print >>sys.stderr, "Error: 2 arguments required"
        print >>sys.stderr, __usage__.strip()
        return 2
    logger = ApplicationLogger(1)
    params = DataStore.params(args[0])
    Localisation.SetApplicationLanguage(params)
    if ToTwitter(params).UploadFile(args[1]):
        return 0
    return 3

if __name__ == "__main__":
    sys.exit(main())
