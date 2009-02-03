#!/usr/bin/env python

import os
import sys

import DataStore
import LogData
import Plot_24Hrs
import Plot_7Days
import Plot_28Days
import Process
import Template
import Upload

def Hourly():
    data_dir = '/home/jim/weather/data'
    template_dir = '/home/jim/weather/templates/'
    work_dir = '/tmp/data/tmp/weather'
    png7_file = os.path.join(work_dir, '7days.png')
    png24_file = os.path.join(work_dir, '24hrs.png')
    png28_file = os.path.join(work_dir, '28days.png')
    uploads = []
    # open data file stores
    params = DataStore.params(data_dir)
    raw_data = DataStore.data_store(data_dir)
    hourly_data = DataStore.hourly_store(data_dir)
    daily_data = DataStore.daily_store(data_dir)
    # do the processing
    LogData.LogData(params, raw_data)
    print 'Generating hourly and daily summaries'
    Process.Process(params, raw_data, hourly_data, daily_data)
    print "Drawing graphs"
    Plot_7Days.Plot_7Days(params, hourly_data, work_dir, png7_file)
    uploads.append(png7_file)
    Plot_24Hrs.Plot_24Hrs(params, raw_data, hourly_data, work_dir, png24_file)
    uploads.append(png24_file)
    Plot_28Days.Plot_28Days(params, daily_data, hourly_data, work_dir, png28_file)
    uploads.append(png28_file)
    for template in os.listdir(template_dir):
        input_file = os.path.join(template_dir, template)
        if not os.path.isfile(input_file):
            continue
        print "Templating", template
        output_file = os.path.join(work_dir, os.path.basename(template))
        Template.Template(hourly_data, daily_data, input_file, output_file)
        uploads.append(output_file)
    print "Uploading to web site"
    Upload.Upload(params, uploads)
    return 0
if __name__ == "__main__":
    # have three tries before giving up
    for n in range(3):
        try:
            sys.exit(Hourly())
        except Exception, ex:
            print ex
    sys.exit(1)
