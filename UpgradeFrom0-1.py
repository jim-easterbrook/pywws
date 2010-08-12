#!/usr/bin/env python

"""
Upgrade stored weather data from v0.1 to v0.3.
"""

import csv
from datetime import datetime
import getopt
import os
import shutil
import sys

from pywws import DataStore
from pywws import Process

def Upgrade(data_dir):
    # convert raw data files
    years = os.listdir(data_dir)
    for year in years:
        for root, dirs, files in os.walk(os.path.join(data_dir, year), topdown=False):
            print root
            new_root = root.replace(data_dir, os.path.join(data_dir, 'raw'))
            if not os.path.isdir(new_root):
                os.makedirs(new_root)
            for file in files:
                file1 = os.path.join(root, file)
                file2 = os.path.join(new_root, file)
                print '%s -> %s' % (file1, file2)
                reader = csv.reader(open(file1, 'rb'))
                writer = csv.writer(open(file2, 'wb'))
                for line in reader:
                    # convert date string
                    line[0] = DataStore.safestrptime(line[0], "%Y-%m-%dT%H:%M:%S")
                    # interpret other data
                    for n in range(1, len(line) - 1):
                        line[n] = eval(line[n])
                    # convert status from bit pattern to single int
                    s = ''
                    for b in reversed(line[-1]):
                        s += b
                    line[-1] = int(s, 2)
                    # save result
                    writer.writerow(line)
                reader.close()
                writer.close()
                # preserve file date (doesn't seem to work on Asus router)
                shutil.copystat(file1, file2)
                os.unlink(file1)
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
