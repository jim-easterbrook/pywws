#!/usr/bin/env python

"""Get weather data, process it, prepare graphs & text files and
upload to a web site.

Typically run every hour from cron.
Comment out or remove the bits you don't need.

usage: python Hourly.py [options] [data_dir]
options are:
\t-h or --help\t\tdisplay this help
\t-v or --verbose\t\tincrease amount of reassuring messages
data_dir is the root directory of the weather data (default /data/weather)
"""

import getopt
import os
import sys

import DataStore
import Localisation
import LogData
from Plot import GraphPlotter
from WindRose import RosePlotter
import Process
import Template
import Upload

def Hourly(data_dir, verbose=1):
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
    # create a translation object for our locale
    translation = Localisation.GetTranslation(params)
    # get weather station data
    # have three tries before giving up
    for n in range(3):
        try:
            LogData.LogData(params, raw_data, verbose)
            break
        except Exception, ex:
            print >>sys.stderr, ex
    # do the processing
    if verbose > 0:
        print 'Generating summary data'
    Process.Process(params, raw_data, hourly_data, daily_data, monthly_data, verbose)
    plotter = GraphPlotter(
        params, raw_data, hourly_data, daily_data, monthly_data, work_dir,
        translation=translation)
    roseplotter = RosePlotter(
        params, raw_data, hourly_data, daily_data, monthly_data, work_dir,
        translation=translation)
    for template in os.listdir(graph_template_dir):
        input_file = os.path.join(graph_template_dir, template)
        if (template[0] == '.' or template[-1] == '~' or
            not os.path.isfile(input_file)):
            continue
        if verbose > 0:
            print "Graphing", template
        output_file = os.path.join(work_dir, os.path.splitext(template)[0])
        if plotter.DoPlot(input_file, output_file) == 0:
            uploads.append(output_file)
        elif roseplotter.DoPlot(input_file, output_file) == 0:
            uploads.append(output_file)
    for template in os.listdir(template_dir):
        input_file = os.path.join(template_dir, template)
        if (template[0] == '.' or template[-1] == '~' or
            not os.path.isfile(input_file)):
            continue
        if verbose > 0:
            print "Templating", template
        output_file = os.path.join(work_dir, template)
        Template.Template(
            params, raw_data, hourly_data, daily_data,
            monthly_data, input_file, output_file, translation=translation)
        if 'tweet' in template:
            if verbose > 0:
                print "Tweeting"
            import ToTwitter
            # have three tries before giving up
            for n in range(3):
                try:
                    ToTwitter.ToTwitter(params, output_file, translation=translation)
                    break
                except Exception, ex:
                    print >>sys.stderr, ex
            os.unlink(output_file)
        else:
            uploads.append(output_file)
    if verbose > 0:
        print "Uploading to web site"
    # have three tries before giving up
    for n in range(3):
        try:
            Upload.Upload(params, uploads)
            break
        except Exception, ex:
            print >>sys.stderr, ex
    for file in uploads:
        os.unlink(file)
    # uncomment the following 7 lines if you want to upload to Weather Underground
##    import ToUnderground
##    for n in range(3):
##        try:
##            ToUnderground.ToUnderground(params, raw_data, verbose)
##            break
##        except Exception, ex:
##            print >>sys.stderr, ex
    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) > 1:
        print >>sys.stderr, 'Error: 0 or 1 arguments required\n'
        print >>sys.stderr, __doc__.strip()
        return 2
    elif len(args) == 1:
        data_dir = args[0]
    else:
        data_dir = '/data/weather'
    return Hourly(data_dir, verbose)
if __name__ == "__main__":
    sys.exit(main())
