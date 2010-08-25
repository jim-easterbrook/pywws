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

import getopt
import os
import shutil
import sys

import DataStore

def Upload(params, files, verbose=1):
    if eval(params.get('ftp', 'local site', 'False')):
        if verbose > 0:
            print "Copying to local directory"
        # copy to local directory
        directory = params.get(
            'ftp', 'directory', os.path.expanduser('~/public_html/weather/data/'))
        if not os.path.isdir(directory):
            os.makedirs(directory)
        for file in files:
            shutil.copy2(file, directory)
        return 0
    if verbose > 0:
        print "Uploading to web site"
    # get remote site details
    secure = eval(params.get('ftp', 'secure', 'False'))
    site = params.get('ftp', 'site', 'ftp.username.your_isp.co.uk')
    user = params.get('ftp', 'user', 'username')
    password = params.get('ftp', 'password', 'secret')
    directory = params.get('ftp', 'directory', 'public_html/weather/data/')
    # open connection
    if secure:
        # install a logging handler to keep paramiko quiet
        import logging
        class NullHandler(logging.Handler):
            def emit(self, record):
                pass
        h = NullHandler()
        logging.getLogger('paramiko').addHandler(h)
        import paramiko
        transport = paramiko.Transport((site, 22))
        transport.connect(username=user, password=password)
        ftp = paramiko.SFTPClient.from_transport(transport)
    else:
        import ftplib
        ftp = ftplib.FTP(site, user, password)
#        print ftp.getwelcome()
    for file in files:
        target = directory + os.path.basename(file)
        # have three tries before giving up
        for n in range(3):
            try:
                if secure:
                    ftp.put(file, target)
                else:
                    if os.path.splitext(file)[1] in ('.txt', '.xml', '.html'):
                        f = open(file, 'r')
                        ftp.storlines('STOR %s' % (target), f)
                    else:
                        f = open(file, 'rb')
                        ftp.storbinary('STOR %s' % (target), f)
                    f.close()
                break
            except Exception, ex:
                print >>sys.stderr, ex
    if secure:
        ftp.close()
        transport.close()
    else:
        ftp.close()
    return 0
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "h", ['help'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    for o, a in opts:
        if o in ('-h', '--help'):
            print __doc__.strip()
            return 0
    # check arguments
    if len(args) < 2:
        print >>sys.stderr, "Error: at least 2 arguments required"
        print >>sys.stderr, __doc__.strip()
        return 2
    return Upload(DataStore.params(args[0]), args[1:])
if __name__ == "__main__":
    sys.exit(main())
