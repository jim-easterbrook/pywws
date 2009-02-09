#!/usr/bin/env python

"""
Upgrade stored weather data from v0.2 to v0.3.
"""

import csv
from datetime import datetime
import getopt
import os
import shutil
import sys

import DataStore
import Process

def Upgrade(data_dir):
    # delete old format summary files
    print 'Deleting old hourly and daily summaries'
    for summary in ['hourly', 'daily']:
        for root, dirs, files in os.walk(os.path.join(data_dir, summary), topdown=False):
            print root
            for file in files:
                os.unlink(os.path.join(root, file))
            os.rmdir(root)
    # create data summaries
    print 'Generating hourly and daily summaries'
    params = DataStore.params(data_dir)
    raw_data = DataStore.data_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    Process.Process(params, raw_data, hourly_data, daily_data)
    return 0
def usage():
    print >>sys.stderr, 'usage: %s [options] data_directory' % sys.argv[0]
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
    for o, a in opts:
        if o == '--help':
            usage()
            return 0
    # process arguments
    if len(args) != 1:
        print >>sys.stderr, "1 argument required"
        usage()
        return 2
    data_dir = args[0]
    return Upgrade(data_dir)
if __name__ == "__main__":
    sys.exit(main())
