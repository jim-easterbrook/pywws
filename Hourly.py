#!/usr/bin/env python

"""Get weather data, process it, prepare graphs & text files and
upload to a web site.

Typically run every hour from cron.
Comment out or remove the bits you don't need.

usage: python Hourly.py [options] [data_dir]
options are:
\t-h or --help\t\tdisplay this help
data_dir is the root directory of the weather data (default /data/weather)
"""

import getopt
import os
import sys

import DataStore
import LogData
from Plot import GraphPlotter
import Process
import Template
import ToTwitter
import Upload

def Hourly(data_dir):
    # get file locations
    params = DataStore.params(data_dir)
    template_dir = params.get(
        'paths', 'templates', os.path.expanduser('~/weather/templates/'))
    graph_template_dir = params.get(
        'paths', 'graph_templates', os.path.expanduser('~/weather/graph_templates/'))
    work_dir = params.get('paths', 'work', '/tmp/weather')
    uploads = []
    # open data file stores
    raw_data = DataStore.data_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    # get weather station data
    # have three tries before giving up
    for n in range(3):
        try:
            LogData.LogData(params, raw_data)
            break
        except Exception, ex:
            print ex
    # do the processing
    print 'Generating summary data'
    Process.Process(params, raw_data, hourly_data, daily_data, monthly_data)
    plotter = GraphPlotter(raw_data, hourly_data, daily_data, monthly_data, work_dir)
    for template in os.listdir(graph_template_dir):
        input_file = os.path.join(graph_template_dir, template)
        if not os.path.isfile(input_file):
            continue
        print "Graphing", template
        output_file = os.path.join(work_dir, os.path.splitext(template)[0])
        if plotter.DoPlot(input_file, output_file) == 0:
            uploads.append(output_file)
    for template in os.listdir(template_dir):
        input_file = os.path.join(template_dir, template)
        if not os.path.isfile(input_file):
            continue
        print "Templating", template
        output_file = os.path.join(work_dir, template)
        Template.Template(
            hourly_data, daily_data, monthly_data, input_file, output_file)
        if 'tweet' in template:
            print "Tweeting"
            # have three tries before giving up
            for n in range(3):
                try:
                    ToTwitter.ToTwitter(params, output_file)
                    break
                except Exception, ex:
                    print ex
            os.unlink(output_file)
        else:
            uploads.append(output_file)
    print "Uploading to web site"
    # have three tries before giving up
    for n in range(3):
        try:
            Upload.Upload(params, uploads)
            break
        except Exception, ex:
            print ex
    for file in uploads:
        os.unlink(file)
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
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
    # check arguments
    if len(args) > 1:
        print >>sys.stderr, 'Error: 0 or 1 arguments required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    elif len(args) == 1:
        data_dir = args[0]
    else:
        data_dir = '/data/weather'
    return Hourly(data_dir)
if __name__ == "__main__":
    sys.exit(main())
