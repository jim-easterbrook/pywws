#!/usr/bin/env python
"""
Upload files to a directory by ftp.

usage: python Upload.py [options] data_dir file [file...]
options are:
\t-h or --help\t\tdisplay this help
data_dir is the root directory of the weather data
file is a file to be uploaded

Login and ftp site details are read from the weather.ini file in
data_dir.
"""

import ftplib
import getopt
import os
import sys

import DataStore

def Upload(params, files):
    # get ftp site details
    site = params.get('ftp', 'site', 'ftp.username.your_isp.co.uk')
    user = params.get('ftp', 'user', 'username')
    password = params.get('ftp', 'password', 'secret')
    directory = params.get('ftp', 'directory', '/public_html/weather/data')
    ftp = ftplib.FTP(site, user, password)
#    print ftp.getwelcome()
    for file in files:
        target = os.path.basename(file)
        if os.path.splitext(target)[1] in ['.txt']:
            f = open(file, 'r')
            ftp.storlines('STOR %s/%s' % (directory, target), f)
        else:
            f = open(file, 'rb')
            ftp.storbinary('STOR %s/%s' % (directory, target), f)
        f.close()
    ftp.close()
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
    # check arguments
    if len(args) < 2:
        print >>sys.stderr, "Error: at least 2 arguments required"
        print >>sys.stderr, __doc__.strip()
        return 2
    # process options
    for o, a in opts:
        if o == '--help':
            print __doc__.strip()
            return 0
    return Upload(DataStore.params(args[0]), args[1:])
if __name__ == "__main__":
    sys.exit(main())
