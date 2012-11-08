#!/usr/bin/env python

"""Routines to perform common tasks such as plotting gaphs or uploading files."""

from datetime import datetime, timedelta
import logging
import os

from calib import Calib
import Plot
import Template
from TimeZone import Local
from toservice import ToService
import Upload
import WindRose
import YoWindow

class RegularTasks(object):
    def __init__(self, params, calib_data, hourly_data, daily_data, monthly_data):
        self.logger = logging.getLogger('pywws.Tasks.RegularTasks')
        self.params = params
        self.calib_data = calib_data
        self.hourly_data = hourly_data
        self.daily_data = daily_data
        self.monthly_data = monthly_data
        # get directories
        self.work_dir = self.params.get('paths', 'work', '/tmp/weather')
        self.template_dir = self.params.get(
            'paths', 'templates', os.path.expanduser('~/weather/templates/'))
        self.graph_template_dir = self.params.get(
            'paths', 'graph_templates', os.path.expanduser('~/weather/graph_templates/'))
        # create calibration object
        self.calibrator = Calib(self.params)
        # create templater object
        self.templater = Template.Template(
            self.params, self.calib_data, self.hourly_data, self.daily_data,
            self.monthly_data)
        # create plotter objects
        self.plotter = Plot.GraphPlotter(
            self.params, self.calib_data, self.hourly_data, self.daily_data,
            self.monthly_data, self.work_dir)
        self.roseplotter = WindRose.RosePlotter(
            self.params, self.calib_data, self.hourly_data, self.daily_data,
            self.monthly_data, self.work_dir)
        # directory of service uploaders
        self.services = dict()
        # create a YoWindow object
        self.yowindow = YoWindow.YoWindow(self.calib_data)
        # get local time's offset from UTC, without DST
        now = self.calib_data.before(datetime.max)
        if not now:
            now = datetime.utcnow()
        time_offset = Local.utcoffset(now) - Local.dst(now)
        # get daytime end hour, in UTC
        self.day_end_hour = eval(params.get('config', 'day end hour', '21'))
        self.day_end_hour = (self.day_end_hour - (time_offset.seconds / 3600)) % 24
        # convert config from underground/metoffice to new services
        for section in ('live', 'logged', 'hourly', '12 hourly', 'daily'):
            services = eval(self.params.get(section, 'services', '[]'))
            for svc in ('underground', 'metoffice'):
                if self.params.get(section, svc) == 'True':
                    if svc not in services:
                        services.append(svc)
                self.params._config.remove_option(section, svc)
            self.params.set(section, 'services', str(services))
        # create service uploader objects
        for section in ('live', 'logged', 'hourly', '12 hourly', 'daily'):
            for service in eval(self.params.get(section, 'services', '[]')):
                if service not in self.services:
                    self.services[service] = ToService(
                        self.params, self.calib_data, service_name=service)

    def has_live_tasks(self):
        yowindow_file = self.params.get('live', 'yowindow', '')
        if yowindow_file:
            return True
        for template in eval(self.params.get('live', 'twitter', '[]')):
            return True
        for service in eval(self.params.get('live', 'services', '[]')):
            return True
        for template in eval(self.params.get('live', 'plot', '[]')):
            return True
        for template in eval(self.params.get('live', 'text', '[]')):
            return True
        return False

    def do_live(self, data):
        data = self.calibrator.calib(data)
        OK = True
        yowindow_file = self.params.get('live', 'yowindow', '')
        if yowindow_file:
            self.yowindow.write_file(yowindow_file, data)
        for template in eval(self.params.get('live', 'twitter', '[]')):
            if not self.do_twitter(template, data):
                OK = False
        for service in eval(self.params.get('live', 'services', '[]')):
            self.services[service].RapidFire(data, True)
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
            if not Upload.Upload(self.params, uploads):
                OK = False
            for file in uploads:
                os.unlink(file)
        return OK

    def do_tasks(self):
        sections = ['logged']
        now = self.calib_data.before(datetime.max)
        if now:
            now += timedelta(minutes=self.calib_data[now]['delay'])
        else:
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
                if not self.do_twitter(template):
                    OK = False
        for section in sections:
            yowindow_file = self.params.get(section, 'yowindow', '')
            if yowindow_file:
                self.yowindow.write_file(yowindow_file)
                break
        all_services = list()
        for section in sections:
            for service in eval(self.params.get(section, 'services', '[]')):
                if service not in all_services:
                    all_services.append(service)
        for service in all_services:
            self.services[service].Upload(True)
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
            if not Upload.Upload(self.params, uploads):
                OK = False
            for file in uploads:
                os.unlink(file)
        if OK:
            for section in sections:
                self.params.set(section, 'last update', now.isoformat(' '))
        return OK

    def do_twitter(self, template, data=None):
        import ToTwitter
        twitter = ToTwitter.ToTwitter(self.params)
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
