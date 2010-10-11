#!/usr/bin/env python
"""
Post a message to Twitter.

usage: python ToTwitter.py [options] data_dir file
options are:
\t--help\t\tdisplay this help
data_dir is the root directory of the weather data
file is the text file to be uploaded

Authorisation data is read from the weather.ini file in data_dir.
"""

import getopt
import logging
import sys
import tweepy

import DataStore
import Localisation
from Logger import ApplicationLogger

consumer_key = '62moSmU9ERTs0LK0g2xHAg'
consumer_secret = 'ygdXpjr0rDagU3dqULPqXF8GFgUOD6zYDapoHAH9ck'

class ToTwitter(object):
    def __init__(self, params, translation=None):
        self.logger = logging.getLogger('pywws.ToTwitter')
        self.old_ex = None
        if not translation:
            translation = Localisation.GetTranslation(params)
        self.charset = translation.charset()
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
                break
            except Exception, ex:
                e = str(ex)
                if e != self.old_ex:
                    self.logger.error(e)
                    self.old_ex = e
        return 0
    def UploadFile(self, file):
        tweet_file = open(file, 'r')
        tweet = tweet_file.read(140)
        tweet_file.close()
        return self.Upload(tweet)
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    for o, a in opts:
        if o == '--help':
            print __doc__.strip()
            return 0
    # check arguments
    if len(args) != 2:
        print >>sys.stderr, "Error: 2 arguments required"
        print >>sys.stderr, __doc__.strip()
        return 2
    logger = ApplicationLogger(1)
    return ToTwitter(DataStore.params(args[0])).UploadFile(args[1])
if __name__ == "__main__":
    sys.exit(main())
