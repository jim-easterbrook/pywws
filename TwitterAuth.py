#!/usr/bin/env python
"""Authorise pywws to post to your Twitter account
::

%s

This program authorises :py:mod:`pywws.ToTwitter` to post to a Twitter
account. You need to create an account before running
:py:mod:`TwitterAuth`. It opens a web browser window (or gives you a
URL to copy to your web browser) where you log in to your Twitter
account. If the login is successful the browser will display a 7 digit
number which you then copy to :py:mod:`TwitterAuth`.

See :doc:`../guides/twitter` for more detail on using Twitter with
pywws.

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python TwitterAuth.py [options] data_dir
 options are:
  -h or --help       display this help
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import sys
import tweepy
import webbrowser

from pywws import DataStore
from pywws.ToTwitter import consumer_key, consumer_secret

def TwitterAuth(params):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        print 'Failed to get request token.'
        return 1
    if not webbrowser.open(redirect_url, new=2, autoraise=0):
        print 'Please use a web browser to open the following URL'
        print redirect_url
    pin = raw_input('Please enter the PIN shown in your web browser: ').strip()
    try:
        auth.get_access_token(pin)
    except tweepy.TweepError:
        print 'Failed to get access token.'
        return 1
    params.set('twitter', 'key', auth.access_token.key)
    params.set('twitter', 'secret', auth.access_token.secret)
    print 'Success! Authorisation data has been stored in %s' % params._path
    return 0
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
    if len(args) != 1:
        print >>sys.stderr, "Error: 1 argument required"
        print >>sys.stderr, __usage__.strip()
        return 2
    return TwitterAuth(DataStore.params(args[0]))
if __name__ == "__main__":
    sys.exit(main())
