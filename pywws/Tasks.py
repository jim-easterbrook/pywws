#!/usr/bin/env python

"""Routines to perform common tasks such as plotting gaphs or uploading files."""

from datetime import datetime, timedelta
import logging
import os

import Plot
import Template
from TimeZone import Local
import ToUnderground
import Upload
import WindRose
import YoWindow

class RegularTasks(object):
    def __init__(self, params, raw_data, hourly_data, daily_data, monthly_data,
                 translation):
        self.logger = logging.getLogger('pywws.Tasks.RegularTasks')
        self.params = params
        self.raw_data = raw_data
        self.hourly_data = hourly_data
        self.daily_data = daily_data
        self.monthly_data = monthly_data
        self.translation = translation
        # get directories
        self.work_dir = self.params.get('paths', 'work', '/tmp/weather')
        self.template_dir = self.params.get(
            'paths', 'templates', os.path.expanduser('~/weather/templates/'))
        self.graph_template_dir = self.params.get(
            'paths', 'graph_templates', os.path.expanduser('~/weather/graph_templates/'))
        # create templater object
        self.templater = Template.Template(
            self.params, self.raw_data, self.hourly_data, self.daily_data,
            self.monthly_data)
        # create plotter objects
        self.plotter = Plot.GraphPlotter(
            self.params, self.raw_data, self.hourly_data, self.daily_data,
            self.monthly_data, self.work_dir, translation=self.translation)
        self.roseplotter = WindRose.RosePlotter(
            self.params, self.raw_data, self.hourly_data, self.daily_data,
            self.monthly_data, self.work_dir, translation=self.translation)
        # create a ToUnderground object
        self.underground = ToUnderground.ToUnderground(self.params, self.raw_data)
        # create a YoWindow object
        self.yowindow = YoWindow.YoWindow(self.params, self.raw_data)
        # get local time's offset from UTC, without DST
        now = self.raw_data.before(datetime.max)
        if not now:
            now = datetime.utcnow()
        time_offset = Local.utcoffset(now) - Local.dst(now)
        # get daytime end hour, in UTC
        self.day_end_hour = eval(params.get('config', 'day end hour', '21'))
        self.day_end_hour = (self.day_end_hour - (time_offset.seconds / 3600)) % 24
    def do_live(self, data):
        OK = True
        yowindow_file = self.params.get('live', 'yowindow', '')
        if yowindow_file:
            self.yowindow.write_file(yowindow_file, data)
        for template in eval(self.params.get('live', 'twitter', '[]')):
            OK = OK and self.do_twitter(template, data)
        if eval(self.params.get('live', 'underground', 'False')):
            OK = OK and self.underground.RapidFire(data, True)
        uploads = []
        for template in eval(self.params.get('live', 'plot', '[]')):
            upload = self.do_plot(template)
            if upload and upload not in uploads:
                uploads.append(upload)
        for template in eval(self.params.get('live', 'text', '[]')):
            upload = self.do_template(template, data)
            if upload not in uploads:
                uploads.append(upload)
        if uploads:
            OK = OK and Upload.Upload(self.params, uploads)
            for file in uploads:
                os.unlink(file)
        return OK
    def do_tasks(self):
        sections = ['logged']
        now = self.raw_data.before(datetime.max)
        if not now:
            now = datetime.utcnow()
        threshold = now.replace(minute=0, second=0, microsecond=0)
        last_update = self.params.get_datetime('hourly', 'last update')
        if (not last_update) or (last_update < threshold):
            # time to do hourly tasks
            sections.append('hourly')
            # set 12 hourly threshold
            threshold -= timedelta(hours=(threshold.hour - self.day_end_hour) % 12)
            last_update = self.params.get_datetime('12 hourly', 'last update')
            if (not last_update) or (last_update < threshold):
                # time to do 12 hourly tasks
                sections.append('12 hourly')
            # set daily threshold
            threshold -= timedelta(hours=(threshold.hour - self.day_end_hour) % 24)
            last_update = self.params.get_datetime('daily', 'last update')
            if (not last_update) or (last_update < threshold):
                # time to do daily tasks
                sections.append('daily')
        OK = True
        for section in sections:
            for template in eval(self.params.get(section, 'twitter', '[]')):
                OK = OK and self.do_twitter(template)
        for section in sections:
            yowindow_file = self.params.get(section, 'yowindow', '')
            if yowindow_file:
                self.yowindow.write_file(yowindow_file)
                break
        for section in sections:
            if eval(self.params.get(section, 'underground', 'False')):
                OK = OK and self.underground.Upload(True)
                break
        uploads = []
        for section in sections:
            for template in eval(self.params.get(section, 'plot', '[]')):
                upload = self.do_plot(template)
                if upload and upload not in uploads:
                    uploads.append(upload)
            for template in eval(self.params.get(section, 'text', '[]')):
                upload = self.do_template(template)
                if upload not in uploads:
                    uploads.append(upload)
        if uploads:
            OK = OK and Upload.Upload(self.params, uploads)
            for file in uploads:
                os.unlink(file)
        if OK:
            for section in sections:
                self.params.set(section, 'last update', now.isoformat(' '))
        return OK
    def do_twitter(self, template, data=None):
        import ToTwitter
        twitter = ToTwitter.ToTwitter(self.params, translation=self.translation)
        self.logger.info("Templating %s", template)
        input_file = os.path.join(self.template_dir, template)
        tweet = self.templater.make_text(input_file, live_data=data)
        self.logger.info("Tweeting")
        return twitter.Upload(tweet[:140])
    def do_plot(self, template):
        self.logger.info("Graphing %s", template)
        input_file = os.path.join(self.graph_template_dir, template)
        output_file = os.path.join(self.work_dir, os.path.splitext(template)[0])
        if self.plotter.DoPlot(input_file, output_file) == 0:
            return output_file
        elif self.roseplotter.DoPlot(input_file, output_file) == 0:
            return output_file
        return None
    def do_template(self, template, data=None):
        self.logger.info("Templating %s", template)
        input_file = os.path.join(self.template_dir, template)
        output_file = os.path.join(self.work_dir, template)
        self.templater.make_file(input_file, output_file, live_data=data)
        return output_file
