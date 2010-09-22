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

def ToTwitter(params, file, translation=None):
    logger = logging.getLogger('pywws.ToTwitter')
    key = params.get('twitter', 'key')
    secret = params.get('twitter', 'secret')
    if (not key) or (not secret):
        logger.error('Authentication data not found')
        return 1
    lat = params.get('twitter', 'latitude')
    long = params.get('twitter', 'longitude')
    tweet_file = open(file, 'r')
    tweet = tweet_file.read(140)
    tweet_file.close()
    if len(tweet) > 0:
        if not translation:
            translation = Localisation.GetTranslation(params)
        charset = translation.charset()
        # assume that systems with no declared charset actually use iso-8859-1
        # so tweets can contain the very useful degree symbol
        if charset in (None, 'ASCII'):
            charset = 'iso-8859-1'
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(key, secret)
        api = tweepy.API(auth)
        for i in range(3):
            try:
                status = api.update_status(tweet.decode(charset), lat=lat, long=long)
                break
            except Exception, ex:
                logger.error(str(ex))
    return 0
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
    return ToTwitter(DataStore.params(args[0]), args[1])
if __name__ == "__main__":
    sys.exit(main())
