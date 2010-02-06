#!/usr/bin/env python
"""
Post a message to Twitter.

usage: python ToTwitter.py [options] data_dir file
options are:
\t--help\t\tdisplay this help
data_dir is the root directory of the weather data
file is the text file to be uploaded

Username and password are read from the weather.ini file in data_dir.
"""

import getopt
import os
import sys
import twitter

import DataStore
from Localisation import charset

def ToTwitter(params, file):
    username = params.get('twitter', 'username', 'twitterusername')
    password = params.get('twitter', 'password', 'twitterpassword')
    tweet_file = open(file, 'r')
    tweet = tweet_file.read(140)
    tweet_file.close()
    if len(tweet) > 0:
        api = twitter.Api(username=username, password=password,
                          input_encoding=charset)
        if hasattr(api, 'SetSource'):
            api.SetSource('pywws')
        for i in range(3):
            try:
                status = api.PostUpdate(tweet)
                break
            except Exception, ex:
                print >>sys.stderr, ex
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
    return ToTwitter(DataStore.params(args[0]), args[1])
if __name__ == "__main__":
    sys.exit(main())
