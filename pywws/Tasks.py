#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Routines to perform common tasks such as plotting gaphs or uploading files."""

from datetime import datetime, timedelta
import logging
import os
import shutil

from pywws.calib import Calib
from pywws import Plot
from pywws import Template
from pywws.TimeZone import Local
from pywws.toservice import ToService
from pywws import Upload
from pywws import WindRose
from pywws import YoWindow

class RegularTasks(object):
    def __init__(self, params, status,
                 calib_data, hourly_data, daily_data, monthly_data):
        self.logger = logging.getLogger('pywws.Tasks.RegularTasks')
        self.params = params
        self.status = status
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
        self.local_dir = self.params.get(
            'paths', 'local_files', os.path.expanduser('~/weather/results/'))
        # create calibration object
        self.calibrator = Calib(self.params, self.status)
        # create templater object
        self.templater = Template.Template(
            self.params, self.status, self.calib_data, self.hourly_data,
            self.daily_data, self.monthly_data)
        # create plotter objects
        self.plotter = Plot.GraphPlotter(
            self.params, self.status, self.calib_data, self.hourly_data,
            self.daily_data, self.monthly_data, self.work_dir)
        self.roseplotter = WindRose.RosePlotter(
            self.params, self.status, self.calib_data, self.hourly_data,
            self.daily_data, self.monthly_data, self.work_dir)
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
        self.day_end_hour = (self.day_end_hour - (time_offset.seconds // 3600)) % 24
        # create service uploader objects
        for section in ('live', 'logged', 'hourly', '12 hourly', 'daily'):
            for service in eval(self.params.get(section, 'services', '[]')):
                if service not in self.services:
                    self.services[service] = ToService(
                        self.params, self.status, self.calib_data,
                        service_name=service)

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

    def _parse_templates(self, section, option):
        for template in eval(self.params.get(section, option, '[]')):
            if isinstance(template, (list, tuple)):
                yield template
            else:
                yield template, ''

    def do_live(self, data):
        data = self.calibrator.calib(data)
        OK = True
        yowindow_file = self.params.get('live', 'yowindow', '')
        if yowindow_file:
            self.yowindow.write_file(yowindow_file, data)
        for template, flags in self._parse_templates('live', 'twitter'):
            if not self.do_twitter(template, data):
                OK = False
        for service in eval(self.params.get('live', 'services', '[]')):
            self.services[service].RapidFire(data, True)
        uploads = []
        local_files = []
        for template, flags in self._parse_templates('live', 'plot'):
            upload = self.do_plot(template)
            if not upload:
                continue
            if 'L' in flags:
                local_files.append(upload)
            else:
                uploads.append(upload)
        for template, flags in self._parse_templates('live', 'text'):
            upload = self.do_template(template, data)
            if 'L' in flags:
                local_files.append(upload)
            else:
                uploads.append(upload)
        if local_files:
            if not os.path.isdir(self.local_dir):
                os.makedirs(self.local_dir)
            for file in local_files:
                shutil.move(file, self.local_dir)
        if uploads:
            if not Upload.Upload(self.params, uploads):
                OK = False
            for file in uploads:
                os.unlink(file)
        return OK

    def do_tasks(self):
        sections = ['logged']
        self.params.unset('logged', 'last update')
        now = self.calib_data.before(datetime.max)
        if now:
            now += timedelta(minutes=self.calib_data[now]['delay'])
        else:
            now = datetime.utcnow()
        threshold = now.replace(minute=0, second=0, microsecond=0)
        last_update = self.params.get_datetime('hourly', 'last update')
        if last_update:
            self.params.unset('hourly', 'last update')
            self.status.set('last update', 'hourly', last_update.isoformat(' '))
        last_update = self.status.get_datetime('last update', 'hourly')
        if (not last_update) or (last_update < threshold):
            # time to do hourly tasks
            sections.append('hourly')
            # set 12 hourly threshold
            threshold -= timedelta(hours=(threshold.hour - self.day_end_hour) % 12)
            last_update = self.params.get_datetime('12 hourly', 'last update')
            if last_update:
                self.params.unset('12 hourly', 'last update')
                self.status.set('last update', '12 hourly', last_update.isoformat(' '))
            last_update = self.status.get_datetime('last update', '12 hourly')
            if (not last_update) or (last_update < threshold):
                # time to do 12 hourly tasks
                sections.append('12 hourly')
            # set daily threshold
            threshold -= timedelta(hours=(threshold.hour - self.day_end_hour) % 24)
            last_update = self.params.get_datetime('daily', 'last update')
            if last_update:
                self.params.unset('daily', 'last update')
                self.status.set('last update', 'daily', last_update.isoformat(' '))
            last_update = self.status.get_datetime('last update', 'daily')
            if (not last_update) or (last_update < threshold):
                # time to do daily tasks
                sections.append('daily')
        OK = True
        for section in sections:
            for template, flags in self._parse_templates(section, 'twitter'):
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
        local_files = []
        for section in sections:
            for template, flags in self._parse_templates(section, 'plot'):
                upload = self.do_plot(template)
                if not upload:
                    continue
                if 'L' in flags:
                    local_files.append(upload)
                else:
                    uploads.append(upload)
            for template, flags in self._parse_templates(section, 'text'):
                upload = self.do_template(template)
                if 'L' in flags:
                    local_files.append(upload)
                else:
                    uploads.append(upload)
        if local_files:
            if not os.path.isdir(self.local_dir):
                os.makedirs(self.local_dir)
            for file in local_files:
                shutil.move(file, self.local_dir)
        if uploads:
            if not Upload.Upload(self.params, uploads):
                OK = False
            for file in uploads:
                os.unlink(file)
        if OK:
            for section in sections:
                self.status.set('last update', section, now.isoformat(' '))
        if 'hourly' in sections:
            # save any unsaved data
            self.params.flush()
            self.status.flush()
            self.calib_data.flush()
            self.hourly_data.flush()
            self.daily_data.flush()
            self.monthly_data.flush()
        return OK

    def do_twitter(self, template, data=None):
        from pywws import ToTwitter
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
