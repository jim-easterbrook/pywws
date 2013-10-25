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

from collections import deque
from datetime import datetime, timedelta
import logging
import os
import Queue
import shutil
import threading

from pywws.calib import Calib
from pywws import Plot
from pywws import Template
from pywws.TimeZone import Local
from pywws.toservice import ToService, FIVE_MINS, FIFTY_SECS
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
        # get directories
        self.work_dir = self.params.get('paths', 'work', '/tmp/weather')
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
            os.makedirs(self.uploads_directory)
        # delay creation of a Twitter object until we know it's needed
        self.twitter = None
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
        self.services = {}
        for section in ('live', 'logged', 'hourly', '12 hourly', 'daily'):
            for name in eval(self.params.get(section, 'services', '[]')):
                if name not in self.services:
                    self.services[name] = ToService(
                        self.params, self.status, self.calib_data,
                        service_name=name)
        if self.asynch:
            self.service_start = {}
            self.service_queued = {}
            for name in self.services:
                self.service_start[name] = self.services[name].catchup_start()
                self.service_queued[name] = 0
        # start asynchronous thread to do uploads
        if self.asynch:
            self.logger.info('Starting asynchronous thread')
            self.uploads_lock = threading.Lock()
            self.to_thread = Queue.Queue()
            self.from_thread = Queue.Queue()
            self.thread = threading.Thread(target=self._asynch_thread)
            self.thread.start()

    def stop_thread(self):
        if not self.asynch:
            return
        self.to_thread.put(('shutdown',))
        self.thread.join()

    def _asynch_thread(self):
        service_queue = {}
        uploads_pending = True
        tweet_queue = deque()
        running = True
        try:
            while running:
                timeout = 600
                while True:
                    try:
                        command = self.to_thread.get(timeout=timeout)
                    except Queue.Empty:
                        break
                    if command[0] == 'shutdown':
                        running = False
                        break
                    elif command[0] == 'upload':
                        uploads_pending = True
                    elif command[0] == 'twitter':
                        tweet_queue.append(command[1])
                    elif command[0] == 'service':
                        name, timestamp, coded_data = command[1:]
                        if name not in service_queue:
                            service_queue[name] = deque()
                        service_queue[name].append((timestamp, coded_data))
                    timeout = 5
                self.logger.debug('Doing asynchronous tasks')
                while tweet_queue:
                    tweet = tweet_queue[0]
                    self.logger.info("Tweeting")
                    if self.twitter.Upload(tweet):
                        tweet_queue.popleft()
                for name in service_queue:
                    count = 0
                    while service_queue[name]:
                        timestamp, coded_data = service_queue[name][0]
                        if (len(service_queue[name]) > 1 and
                                            self.services[name].catchup <= 0):
                            # don't send 'catchup' records
                            pass
                        elif self.services[name].send_data(coded_data):
                            count += 1
                        else:
                            break
                        self.from_thread.put(('service', name, timestamp))
                        service_queue[name].popleft()
                    if count > 0:
                        self.services[name].logger.info('%d records sent', count)
                if uploads_pending:
                    self.uploads_lock.acquire()
                    if self._do_uploads():
                        uploads_pending = False
                    self.uploads_lock.release()
        except Exception, ex:
            self.logger.exception(ex)

    def has_live_tasks(self):
        yowindow_file = self.params.get('live', 'yowindow', '')
        if yowindow_file:
            return True
        for template in eval(self.params.get('live', 'twitter', '[]')):
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
        OK = True
        for section in sections:
            yowindow_file = self.params.get(section, 'yowindow', '')
            if yowindow_file:
                self.yowindow.write_file(yowindow_file)
                break
        for section in sections:
            for template, flags in self._parse_templates(section, 'twitter'):
                if not self.do_twitter(template):
                    OK = False
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
                    if not self.do_twitter(template, live_data):
                        OK = False
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
                os.makedirs(self.local_dir)
            for file in local_files:
                targ = os.path.join(
                    self.local_dir, os.path.basename(file))
                if os.path.exists(targ):
                    os.unlink(targ)
                shutil.move(file, self.local_dir)
        if uploads:
            if self.asynch:
                if not self.thread.isAlive():
                    raise RuntimeError('upload thread has terminated')
                self.uploads_lock.acquire()
            for file in uploads:
                targ = os.path.join(
                    self.uploads_directory, os.path.basename(file))
                if os.path.exists(targ):
                    os.unlink(targ)
                shutil.move(file, self.uploads_directory)
            if self.asynch:
                self.uploads_lock.release()
                self.to_thread.put(('upload',))
        if not self.asynch:
            self._do_uploads()
        if self.asynch:
            # process replies from thread
            while True:
                try:
                    message = self.from_thread.get_nowait()
                except Queue.Empty:
                    break
                if message[0] == 'service':
                    name, timestamp = message[1:]
                    self.services[name].set_status(timestamp)
                    self.service_queued[name] -= 1
        return OK

    def do_live(self, data):
        return self._do_common(['live'], self.calibrator.calib(data))

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
        OK = self._do_common(sections)
        if OK:
            for section in sections:
                self.status.set('last update', section, now.isoformat(' '))
        if 'hourly' in sections:
            # save any unsaved data
            self.params.flush()
            self.status.flush()
            self.raw_data.flush()
            self.calib_data.flush()
            self.hourly_data.flush()
            self.daily_data.flush()
            self.monthly_data.flush()
        return OK

    def _do_uploads(self):
        uploads = []
        for name in os.listdir(self.uploads_directory):
            path = os.path.join(self.uploads_directory, name)
            if os.path.isfile(path):
                uploads.append(path)
        if not uploads:
            return True
        OK = True
        self.uploader.connect()
        for path in uploads:
            if self.uploader.upload_file(path):
                os.unlink(path)
            else:
                OK = False
        self.uploader.disconnect()
        return OK

    def _do_service(self, name, live_data):
        service = self.services[name]
        if self.asynch:
            for data in service.next_data(self.service_start[name], live_data):
                if self.service_queued[name] >= 50:
                    break
                coded_data = service.encode_data(data)
                if not coded_data:
                    continue
                self.to_thread.put(('service', name, data['idx'], coded_data))
                self.service_start[name] = data['idx'] + FIFTY_SECS
                parent = service.parent
                if parent:
                    last_update = self.status.get_datetime(
                        'last update', parent)
                    if last_update and last_update >= data['idx'] - FIVE_MINS:
                        self.service_start[parent] = data['idx'] + FIFTY_SECS
                self.service_queued[name] += 1
        else:
            service.Upload(live_data=live_data)

    def do_twitter(self, template, data=None):
        if not self.twitter:
            from pywws import ToTwitter
            self.twitter = ToTwitter.ToTwitter(self.params)
        self.logger.info("Templating %s", template)
        input_file = os.path.join(self.template_dir, template)
        tweet = self.templater.make_text(input_file, live_data=data)[:140]
        if self.asynch:
            self.to_thread.put(('twitter', tweet))
            return True
        else:
            self.logger.info("Tweeting")
            return self.twitter.Upload(tweet)

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
