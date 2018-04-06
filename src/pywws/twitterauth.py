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

"""Authorise pywws to post to your Twitter account
::

%s

This program authorises :py:mod:`pywws.totwitter` to post to a Twitter
account. You need to create an account before running
:py:mod:`twitterauth`. It opens a web browser window (or gives you a
URL to copy to your web browser) where you log in to your Twitter
account. If the login is successful the browser will display a 7 digit
number which you then copy to :py:mod:`twitterauth`.

See :doc:`../guides/twitter` for more detail on using Twitter with
pywws.

"""

from __future__ import absolute_import, print_function

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python -m pywws.twitterauth [options] data_dir
 options are:
  -h or --help       display this help
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import sys
import webbrowser

if sys.version_info[0] >= 3:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl

import oauth2 as oauth

from pywws.constants import Twitter
from pywws import DataStore


def twitter_auth(params):
    consumer = oauth.Consumer(Twitter.consumer_key, Twitter.consumer_secret)
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
        pin = input('Please enter the PIN shown in your web browser: ')
    else:
        pin = raw_input('Please enter the PIN shown in your web browser: ')
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
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error as msg:
        print('Error: %s\n' % msg, file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 1
    # process options
    for o, a in opts:
        if o in ('-h', '--help'):
            print(__usage__.strip())
            return 0
    # check arguments
    if len(args) != 1:
        print("Error: 1 argument required", file=sys.stderr)
        print(__usage__.strip(), file=sys.stderr)
        return 2
    with DataStore.pywws_context(args[0]) as context:
        return twitter_auth(context.params)


if __name__ == "__main__":
    sys.exit(main())
