#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-17  pywws contributors

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

from __future__ import absolute_import

from collections import deque
from datetime import datetime, timedelta
import logging
import os
import shutil
import threading

from pywws.calib import Calib
from pywws import Plot
from pywws import Template
from pywws.TimeZone import STDOFFSET, local_utc_offset
from pywws.toservice import ToService
from pywws import Upload
from pywws import WindRose
from pywws import YoWindow

class RegularTasks(object):
    def __init__(self, params, status,
                 raw_data, calib_data, hourly_data, daily_data, monthly_data,
                 asynch=False):
        self.logger = logging.getLogger('pywws.Tasks.RegularTasks')
        self.params = params
        self.status = status
        self.raw_data = raw_data
        self.calib_data = calib_data
        self.hourly_data = hourly_data
        self.daily_data = daily_data
        self.monthly_data = monthly_data
        self.asynch = asynch
        self.flush = eval(self.params.get('config', 'frequent writes', 'False'))
        # get directories
        self.work_dir = self.params.get('paths', 'work', '/tmp/weather')
        if not os.path.isdir(self.work_dir):
            raise RuntimeError(
                'Directory "' + self.work_dir + '" does not exist.')
        self.template_dir = self.params.get(
            'paths', 'templates', os.path.expanduser('~/weather/templates/'))
        self.graph_template_dir = self.params.get(
            'paths', 'graph_templates', os.path.expanduser('~/weather/graph_templates/'))
        self.local_dir = self.params.get(
            'paths', 'local_files', os.path.expanduser('~/weather/results/'))
        # create calibration object
        self.calibrator = Calib(self.params, self.raw_data)
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
        # create FTP uploader object
        self.uploader = Upload.Upload(self.params)
        self.uploads_directory = os.path.join(self.work_dir, 'uploads')
        if not os.path.isdir(self.uploads_directory):
            os.mkdir(self.uploads_directory)
        # delay creation of a Twitter object until we know it's needed
        self.twitter = None
        # create a YoWindow object
        self.yowindow = YoWindow.YoWindow(self.calib_data)
        # get daytime end hour, in UTC
        self.day_end_hour = eval(params.get('config', 'day end hour', '21'))
        self.day_end_hour = (self.day_end_hour - (STDOFFSET.seconds // 3600)) % 24
        # parse "cron" sections
        self.cron = {}
        for section in self.params._config.sections():
            if section.split()[0] != 'cron':
                continue
            import croniter
            self.cron[section] = croniter.croniter(
                self.params.get(section, 'format', ''))
            self.cron[section].get_prev()
            last_update = self.status.get_datetime('last update', section)
            if last_update:
                last_update = last_update + local_utc_offset(last_update)
                while self.cron[section].get_current(datetime) <= last_update:
                    self.cron[section].get_next()
        # create service uploader objects
        self.services = {}
        for section in self.cron.keys() + [
                       'live', 'logged', 'hourly', '12 hourly', 'daily']:
            for name in eval(self.params.get(section, 'services', '[]')):
                if name not in self.services:
                    self.services[name] = ToService(
                        self.params, self.status, self.calib_data,
                        service_name=name)
            # check for deprecated syntax
            if self.params.get(section, 'twitter') not in (None, '[]'):
                self.logger.warning(
                    'Deprecated twitter entry in [%s]', section)
            if self.params.get(section, 'yowindow'):
                self.logger.warning(
                    'Deprecated yowindow entry in [%s]', section)
        # create queues for things to upload / send
        self.tweet_queue = deque()
        self.service_queue = {}
        for name in self.services:
            self.service_queue[name] = deque()
        self.uploads_queue = deque()
        # start asynchronous thread to do uploads
        if self.asynch:
            self.logger.info('Starting asynchronous thread')
            self.shutdown_thread = threading.Event()
            self.wake_thread = threading.Event()
            self.thread = threading.Thread(target=self._asynch_thread)
            self.thread.start()

    def stop_thread(self):
        if not self.asynch:
            return
        self.shutdown_thread.set()
        self.wake_thread.set()
        self.thread.join()
        self.logger.debug('Asynchronous thread terminated')

    def _asynch_thread(self):
        try:
            while not self.shutdown_thread.isSet():
                timeout = 600
                while True:
                    self.wake_thread.wait(timeout)
                    if not self.wake_thread.isSet():
                        # main thread has stopped putting things on the queue
                        break
                    self.wake_thread.clear()
                    timeout = 2
                self.logger.debug('Doing asynchronous tasks')
                self._do_queued_tasks()
        except Exception, ex:
            self.logger.exception(ex)

    def _do_queued_tasks(self):
        while self.tweet_queue:
            tweet = self.tweet_queue[0]
            self.logger.info("Tweeting")
            if not self.twitter.Upload(tweet):
                break
            self.tweet_queue.popleft()
        for name in self.service_queue:
            service = self.services[name]
            count = 0
            while self.service_queue[name]:
                timestamp, prepared_data = self.service_queue[name][0]
                if len(self.service_queue[name]) > 1 and service.catchup <= 0:
                    # don't send queued 'catchup' records
                    pass
                elif service.send_data(timestamp, prepared_data):
                    count += 1
                else:
                    break
                self.service_queue[name].popleft()
            if count > 0:
                service.logger.info('%d records sent', count)
        while self.uploads_queue:
            file = self.uploads_queue.popleft()
            if not os.path.exists(file):
                continue
            targ = os.path.join(self.uploads_directory, os.path.basename(file))
            if os.path.exists(targ):
                os.unlink(targ)
            shutil.move(file, self.uploads_directory)
        self._do_uploads()

    def has_live_tasks(self):
        if self.cron:
            return True
        yowindow_file = self.params.get('live', 'yowindow')
        if yowindow_file:
            return True
        if self.params.get('live', 'twitter') not in (None, '[]'):
            return True
        for name in eval(self.params.get('live', 'services', '[]')):
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

    def _do_common(self, sections, live_data=None):
        if self.asynch and not self.thread.isAlive():
            raise RuntimeError('Asynchronous thread terminated unexpectedly')
        for section in sections:
            yowindow_file = self.params.get(section, 'yowindow')
            if yowindow_file:
                self.yowindow.write_file(yowindow_file)
                break
        for section in sections:
            templates = self.params.get(section, 'twitter')
            if templates not in (None, '[]'):
                for template in eval(templates):
                    self.do_twitter(template)
        uploads = []
        local_files = []
        service_done = []
        for section in sections:
            for name in eval(self.params.get(section, 'services', '[]')):
                if name not in service_done:
                    self._do_service(name, live_data)
                    service_done.append(name)
            for template, flags in self._parse_templates(section, 'text'):
                if 'T' in flags:
                    self.do_twitter(template, live_data)
                    continue
                upload = self.do_template(template, live_data)
                if 'L' in flags:
                    if upload not in local_files:
                        local_files.append(upload)
                elif upload not in uploads:
                    uploads.append(upload)
            for template, flags in self._parse_templates(section, 'plot'):
                upload = self.do_plot(template)
                if not upload:
                    continue
                if 'L' in flags:
                    if upload not in local_files:
                        local_files.append(upload)
                elif upload not in uploads:
                    uploads.append(upload)
        if local_files:
            if not os.path.isdir(self.local_dir):
                raise RuntimeError(
                    'Directory "' + self.local_dir + '" does not exist.')
            for file in local_files:
                targ = os.path.join(
                    self.local_dir, os.path.basename(file))
                if os.path.exists(targ):
                    os.unlink(targ)
                shutil.move(file, self.local_dir)
        for file in uploads:
            self.uploads_queue.append(file)
        if self.asynch:
            self.wake_thread.set()
        else:
            self._do_queued_tasks()

    def _do_cron(self, live_data=None):
        if not self.cron:
            return
        # get timestamp of latest data
        if live_data:
            now = live_data['idx']
        else:
            now = self.calib_data.before(datetime.max)
        if not now:
            now = datetime.utcnow()
        # convert to local time
        local_now = now + local_utc_offset(now)
        # get list of due sections
        sections = []
        for section in self.cron:
            if self.cron[section].get_current(datetime) > local_now:
                continue
            sections.append(section)
            while self.cron[section].get_current(datetime) <= local_now:
                self.cron[section].get_next()
        if not sections:
            return
        # do it!
        self._do_common(sections, live_data)
        for section in sections:
            self.status.set('last update', section, now.isoformat(' '))

    def do_live(self, data):
        calib_data = self.calibrator.calib(data)
        self._do_common(['live'], calib_data)
        self._do_cron(calib_data)

    def do_tasks(self):
        sections = ['logged']
        self.params.unset('logged', 'last update')
        now = self.calib_data.before(datetime.max)
        if now:
            now += timedelta(minutes=self.calib_data[now]['delay'])
        else:
            now = datetime.utcnow().replace(microsecond=0)
        threshold = (now + STDOFFSET).replace(minute=0, second=0) - STDOFFSET
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
        self._do_common(sections)
        for section in sections:
            self.status.set('last update', section, now.isoformat(' '))
        self._do_cron()
        if self.flush or 'hourly' in sections:
            # save any unsaved data
            self.params.flush()
            self.status.flush()
            self.raw_data.flush()
            self.calib_data.flush()
            self.hourly_data.flush()
            self.daily_data.flush()
            self.monthly_data.flush()

    def _do_uploads(self):
        if not os.path.isdir(self.uploads_directory):
            return True
        # get list of pending uploads
        uploads = []
        for name in os.listdir(self.uploads_directory):
            path = os.path.join(self.uploads_directory, name)
            if os.path.isfile(path):
                uploads.append(path)
        if not uploads:
            return True
        # upload files
        if not self.uploader.connect():
            return
        for path in uploads:
            if self.uploader.upload_file(path):
                os.unlink(path)
        self.uploader.disconnect()

    def _do_service(self, name, live_data):
        service = self.services[name]
        if len(self.service_queue[name]) >= 50:
            return
        for data in service.next_data(True, live_data):
            prepared_data = service.prepare_data(data)
            if not prepared_data:
                continue
            self.service_queue[name].append((data['idx'], prepared_data))
            if len(self.service_queue[name]) >= 50:
                break
        if self.asynch:
            self.wake_thread.set()

    def do_twitter(self, template, data=None):
        if not self.twitter:
            from pywws import ToTwitter
            self.twitter = ToTwitter.ToTwitter(self.params)
        self.logger.info("Templating %s", template)
        input_file = os.path.join(self.template_dir, template)
        tweet = self.templater.make_text(input_file, live_data=data)
        self.tweet_queue.append(tweet)
        if self.asynch:
            self.wake_thread.set()

    def do_plot(self, template):
        self.logger.info("Graphing %s", template)
        input_file = os.path.join(self.graph_template_dir, template)
        output_file = os.path.join(self.work_dir, os.path.splitext(template)[0])
        input_xml = Plot.GraphFileReader(input_file)
        if (input_xml.get_children(self.plotter.plot_name) and
                        self.plotter.DoPlot(input_xml, output_file) == 0):
            return output_file
        if (input_xml.get_children(self.roseplotter.plot_name) and
                        self.roseplotter.DoPlot(input_xml, output_file) == 0):
            return output_file
        self.logger.warning('nothing to graph in %s', input_file)
        return None

    def do_template(self, template, data=None):
        self.logger.info("Templating %s", template)
        input_file = os.path.join(self.template_dir, template)
        output_file = os.path.join(self.work_dir, template)
        self.templater.make_file(input_file, output_file, live_data=data)
        return output_file
