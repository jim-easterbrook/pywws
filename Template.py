#!/usr/bin/env python
"""
Create text data file based on a template.

usage: python Template.py [options] data_dir template_file output_file
options are:
\t--help\t\tdisplay this help
data_dir is the root directory of the weather data
template_file is the template text source file
output_file is the name of the text file to be created
"""

from datetime import datetime, timedelta
import getopt
import os
import shlex
import sys

import DataStore
from TimeZone import Local, utc
from WeatherStation import pressure_trend_text, wind_dir_text

def Template(hourly_data, daily_data, template_file, output_file):
    def jump(idx, count):
        while count > 0:
            new_idx = data_set.after(idx + timedelta(seconds=1))
            if new_idx == None:
                break
            idx = new_idx
            count -= 1
        while count < 0:
            new_idx = data_set.before(idx)
            if new_idx == None:
                break
            idx = new_idx
            count += 1
        return idx
    # start off in hourly data mode
    data_set = hourly_data
    # start off in utc
    time_zone = utc
    # jump to last item
    idx = jump(datetime.max, -1)
    if idx == None:
        print >>sys.stderr, "No summary data - run Process.py first"
        return 4
    data = data_set[idx]
    # open template file and output file
    tmplt = open(template_file, 'r')
    of = open(output_file, 'w')
    # do the text processing
    while True:
        line = tmplt.readline()
        if line == '':
            break
        parts = line.split('#')
        for i in range(len(parts)):
            if i % 2 == 0:
                # not a processing directive
                if parts[i] != '\n':
                    of.write(parts[i])
                continue
            command = shlex.split(parts[i])
            if command == []:
                # empty command == print a single '#'
                of.write('#')
            elif command[0] in data.keys():
                # output a value
                # format is: key fmt_string no_value_string conversion
                # get value
                x = data[command[0]]
                if command[0] == 'wind_dir' and data['wind_ave'] < 0.3:
                    x = None
                # adjust time
                if isinstance(x, datetime):
                    x = x.replace(tzinfo=utc)
                    x = x.astimezone(time_zone)
                # get format
                fmt = '%s'
                if len(command) > 1:
                    fmt = command[1]
                # convert data
                if x != None and len(command) > 3:
                    x = eval(command[3])
                # write output
                if x == None:
                    if len(command) > 2:
                        of.write(command[2])
                elif isinstance(x, datetime):
                    of.write(x.strftime(fmt))
                else:
                    of.write(fmt % (x))
            elif command[0] == 'daily':
                data_set = daily_data
                idx = jump(datetime.max, -1)
                data = data_set[idx]
            elif command[0] == 'hourly':
                data_set = hourly_data
                idx = jump(datetime.max, -1)
                data = data_set[idx]
            elif command[0] == 'timezone':
                if command[1] == 'utc':
                    time_zone = utc
                elif command[1] == 'local':
                    time_zone = Local
                else:
                    print >>sys.stderr, "Unknown time zone: %s" % command[1]
                    return 6
            elif command[0] == 'jump':
                idx = jump(idx, int(command[1]))
                data = data_set[idx]
            elif command[0] == 'loop':
                loop_count = int(command[1])
                loop_start = tmplt.tell()
            elif command[0] == 'endloop':
                loop_count -= 1
                if loop_count > 0:
                    tmplt.seek(loop_start, 0)
            else:
                print >>sys.stderr, "Unknown processing directive:", line
                return 5
    of.close()
    tmplt.close()
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
    if len(args) != 3:
        print >>sys.stderr, 'Error: 3 arguments required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    # process options
    for o, a in opts:
        if o == '--help':
            print __doc__.strip()
            return 0
    return Template(DataStore.hourly_store(args[0]),
                    DataStore.daily_store(args[0]), args[1], args[2])
if __name__ == "__main__":
    sys.exit(main())
