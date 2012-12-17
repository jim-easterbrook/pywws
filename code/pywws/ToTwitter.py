#!/usr/bin/env python
"""Post a message to Twitter
::

%s

This module posts a brief message to `Twitter
<https://twitter.com/>`_. Before posting to Twitter you need to set up
an account and then authorise pywws by running the
:py:mod:`TwitterAuth` program. See :doc:`../guides/twitter` for
detailed instructions.

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python RunModule.py ToTwitter [options] data_dir file
 options are:
  -h | --help  display this help
 data_dir is the root directory of the weather data
 file is the text file to be uploaded
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import logging
import sys
import tweepy

from . import DataStore
from . import Localisation
from .Logger import ApplicationLogger

consumer_key = '62moSmU9ERTs0LK0g2xHAg'
consumer_secret = 'ygdXpjr0rDagU3dqULPqXF8GFgUOD6zYDapoHAH9ck'

class ToTwitter(object):
    def __init__(self, params):
        self.logger = logging.getLogger('pywws.ToTwitter')
        self.old_ex = None
        self.charset = Localisation.translation.charset()
        # assume that systems with no declared charset actually use iso-8859-1
        # so tweets can contain the very useful degree symbol
        if self.charset in (None, 'ASCII'):
            self.charset = 'iso-8859-1'
        # get parameters
        key = params.get('twitter', 'key')
        secret = params.get('twitter', 'secret')
        if (not key) or (not secret):
            raise RuntimeError('Authentication data not found')
        self.lat = params.get('twitter', 'latitude')
        self.long = params.get('twitter', 'longitude')
        # open API
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(key, secret)
        self.api = tweepy.API(auth)

    def Upload(self, tweet):
        if not tweet:
            return 0
        for i in range(3):
            try:
                status = self.api.update_status(
                    tweet.decode(self.charset), lat=self.lat, long=self.long)
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
        if sys.version_info[0] >= 3:
            tweet_file = open(file, 'r', encoding=self.charset)
        else:
            tweet_file = open(file, 'r')
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
