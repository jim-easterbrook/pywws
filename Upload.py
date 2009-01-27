#!/usr/bin/env python

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
def usage():
    print >>sys.stderr, 'usage: %s [options] data_dir file [file...]' % sys.argv[0]
    print >>sys.stderr, '''\toptions are:
    \t--help\t\t\tdisplay this help'''
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, msg
        usage()
        return 1
    # process options
    start = None
    stop = None
    for o, a in opts:
        if o == '--help':
            usage()
            return 0
    # process arguments
    if len(args) < 2:
        print >>sys.stderr, "at least 2 arguments required"
        usage()
        return 2
    return Upload(DataStore.params(args[0]), args[1:])
if __name__ == "__main__":
    sys.exit(main())