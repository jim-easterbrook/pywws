#!/usr/bin/env python

"""Get weather data, process it, prepare graphs & text files and
upload to a web site.

Typically run every hour from cron.

Comment out or remove the bits you don't need.
"""

import os
import sys

import DataStore
import LogData
import Plot
import Process
import Template
import ToTwitter
import Upload

def Hourly():
    data_dir = '/data/weather'
    template_dir = '/home/jim/weather/templates/'
    graph_template_dir = '/home/jim/weather/graph_templates/'
    work_dir = '/data/tmp/weather'
    uploads = []
    # open data file stores
    params = DataStore.params(data_dir)
    raw_data = DataStore.data_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    monthly_data = DataStore.monthly_store(data_dir)
    # do the processing
    LogData.LogData(params, raw_data)
    print 'Generating summary data'
    Process.Process(params, raw_data, hourly_data, daily_data, monthly_data)
    for template in os.listdir(graph_template_dir):
        input_file = os.path.join(graph_template_dir, template)
        if not os.path.isfile(input_file):
            continue
        print "Graphing", template
        output_file = os.path.join(work_dir, os.path.splitext(template)[0])
        Plot.Plot(params, raw_data, hourly_data, daily_data, monthly_data,
                  work_dir, input_file, output_file)
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
            ToTwitter.ToTwitter(params, output_file)
        else:
            uploads.append(output_file)
    print "Uploading to web site"
    Upload.Upload(params, uploads)
    for file in uploads:
        os.unlink(file)
    return 0
if __name__ == "__main__":
    # have three tries before giving up
    for n in range(3):
        try:
            sys.exit(Hourly())
        except Exception, ex:
            print ex
    sys.exit(1)
