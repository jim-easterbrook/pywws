# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-18  pywws contributors

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

from datetime import datetime, timedelta
import importlib
import logging
import os
import sys

from pywws.calib import Calib
import pywws.plot
import pywws.template
from pywws.timezone import timezone
import pywws.towebsite
import pywws.windrose

logger = logging.getLogger(__name__)


class RegularTasks(object):
    def __init__(self, context):
        self.context = context
        self.params = context.params
        self.status = context.status
        self.raw_data = context.raw_data
        self.calib_data = context.calib_data
        self.hourly_data = context.hourly_data
        self.daily_data = context.daily_data
        self.monthly_data = context.monthly_data
        self.flush = eval(self.params.get('config', 'frequent writes', 'False'))
        # get directories
        self.work_dir = self.params.get('paths', 'work', '/tmp/pywws')
        if not os.path.isdir(self.work_dir):
            os.makedirs(self.work_dir)
        self.template_dir = self.params.get(
            'paths', 'templates', os.path.expanduser('~/weather/templates/'))
        self.graph_template_dir = self.params.get(
            'paths', 'graph_templates', os.path.expanduser('~/weather/graph_templates/'))
        self.local_dir = self.params.get(
            'paths', 'local_files', os.path.expanduser('~/weather/results/'))
        self.module_dir = self.params.get(
            'paths', 'modules', os.path.expanduser('~/weather/modules/'))
        # create calibration object
        self.calibrator = Calib(self.params, self.raw_data)
        # create templater object
        self.templater = pywws.template.Template(context)
        # create plotter objects
        self.plotter = pywws.plot.GraphPlotter(context, self.work_dir)
        self.roseplotter = pywws.windrose.RosePlotter(context, self.work_dir)
        # create FTP uploads directory
        self.uploads_directory = os.path.join(self.work_dir, 'uploads')
        if not os.path.isdir(self.uploads_directory):
            os.makedirs(self.uploads_directory)
        # delay creation of uploader object until we know it's needed
        self.uploader = None
        # delay creation of a Twitter object until we know it's needed
        self.twitter = None
        # get daytime end hour
        self.day_end_hour, self.use_dst = pywws.process.get_day_end_hour(
                                                                self.params)
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
                last_update += timezone.utcoffset(last_update)
                while self.cron[section].get_current(datetime) <= last_update:
                    self.cron[section].get_next()
        # create service uploader objects
        self.services = {}
        for section in list(self.cron.keys()) + [
                       'live', 'logged', 'hourly', '12 hourly', 'daily']:
            for name in eval(self.params.get(section, 'services', '[]')):
                if name in self.services:
                    continue
                if os.path.exists(os.path.join(self.module_dir, name + '.py')):
                    sys.path.insert(0, self.module_dir)
                    mod = importlib.import_module(name)
                    del sys.path[0]
                else:
                    mod = importlib.import_module('pywws.service.' + name)
                self.services[name] = mod.ToService(context)
            # check for obsolete entries
            if self.params.get(section, 'twitter'):
                logger.error(
                    'Obsolete twitter entry in weather.ini [%s]', section)
            if self.params.get(section, 'yowindow'):
                logger.error(
                    'Obsolete yowindow entry in weather.ini [%s]', section)
        # check for 'local' template results
        if os.path.isdir(self.local_dir):
            return
        has_local = False
        for section in list(self.cron.keys()) + [
                       'live', 'logged', 'hourly', '12 hourly', 'daily']:
            for template, flags in self._parse_templates(section, 'text'):
                if 'L' in flags:
                    has_local = True
            for template, flags in self._parse_templates(section, 'plot'):
                if 'L' in flags:
                    has_local = True
            if has_local:
                os.makedirs(self.local_dir)
                break

    def has_live_tasks(self):
        if self.cron:
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

    def _do_common(self, now, sections, live_data=None):
        logger.info('doing task sections {!r}'.format(sections))
        # make lists of tasks from all sections, avoiding repeats
        service_tasks = []
        text_tasks = []
        plot_tasks = []
        for section in sections:
            for name in eval(self.params.get(section, 'services', '[]')):
                if name not in service_tasks:
                    service_tasks.append(name)
            for task in self._parse_templates(section, 'text'):
                if task not in text_tasks:
                    text_tasks.append(task)
            for task in self._parse_templates(section, 'plot'):
                if task not in plot_tasks:
                    plot_tasks.append(task)
        # do service tasks
        for name in service_tasks:
            if name in self.services:
                self.services[name].upload(live_data=live_data)
        # do plot templates
        for template, flags in plot_tasks:
            self.do_plot(template, local='L' in flags)
        # do text templates
        for template, flags in text_tasks:
            if 'T' in flags:
                self.do_twitter(template, live_data)
                continue
            self.do_template(template, data=live_data, local='L' in flags)
        # upload non local files
        upload_files = []
        for name in os.listdir(self.uploads_directory):
            path = os.path.join(self.uploads_directory, name)
            if os.path.isfile(path):
                upload_files.append(path)
        if upload_files:
            if not self.uploader:
                self.uploader = pywws.towebsite.ToWebSite(self.context)
            self.uploader.upload(upload_files, delete=True)
        # update status
        for section in sections:
            self.status.set('last update', section, now.isoformat(' '))
        # save any unsaved data
        if self.flush or 'hourly' in sections:
            self.context.flush()

    def _cron_due(self, now):
        if not self.cron:
            return []
        # convert now to local time
        local_now = now + timezone.utcoffset(now)
        # make list of due sections
        sections = []
        for section in self.cron:
            if self.cron[section].get_current(datetime) > local_now:
                continue
            sections.append(section)
            while self.cron[section].get_current(datetime) <= local_now:
                self.cron[section].get_next()
        return sections

    def _periodic_due(self, now):
        # get start of current hour, allowing for odd time zones
        threshold = timezone.local_replace(now, minute=0, second=0)
        # make list of due sections
        sections = []
        # hourly
        last_update = self.status.get_datetime('last update', 'hourly')
        if not last_update or last_update < threshold:
            sections.append('hourly')
        # daily
        threshold = timezone.local_replace(
            threshold, use_dst=self.use_dst, hour=self.day_end_hour)
        last_update = self.status.get_datetime('last update', 'daily')
        if not last_update or last_update < threshold:
            sections.append('daily')
        # 12 hourly == daily
        last_update = self.status.get_datetime('last update', '12 hourly')
        if not last_update or last_update < threshold:
            sections.append('12 hourly')
            return sections
        # 12 hourly == daily +- 12 hours
        threshold = timezone.local_replace(
            now, use_dst=self.use_dst,
            hour=((self.day_end_hour + 12) % 24), minute=0, second=0)
        if last_update < threshold:
            sections.append('12 hourly')
        return sections

    def do_live(self, data):
        calib_data = self.calibrator.calib(data)
        now = calib_data['idx']
        sections = ['live'] + self._cron_due(now) + self._periodic_due(now)
        self._do_common(now, sections, live_data=calib_data)

    def do_tasks(self):
        now = self.calib_data.before(datetime.max)
        if not now:
            raise RuntimeError('No processed data available')
        if not self.context.live_logging:
            # do periodic tasks if they would be due by next logging time
            now += timedelta(minutes=self.calib_data[now]['delay'])
        sections = ['logged'] + self._cron_due(now) + self._periodic_due(now)
        self._do_common(now, sections)
        if not self.context.live_logging:
            # cleanly shut down upload threads
            for name in self.services:
                self.services[name].stop()
            if self.twitter:
                self.twitter.stop()
            if self.uploader:
                self.uploader.stop()

    def do_twitter(self, template, data=None):
        if not self.twitter:
            import pywws.totwitter
            self.twitter = pywws.totwitter.ToTwitter(self.context)
        logger.info("Templating %s", template)
        input_file = os.path.join(self.template_dir, template)
        tweet = self.templater.make_text(input_file, live_data=data)
        logger.info("Tweeting")
        self.twitter.upload(tweet)

    def do_plot(self, template, local=False):
        logger.info("Graphing %s", template)
        input_file = os.path.join(self.graph_template_dir, template)
        output_file = os.path.splitext(template)[0]
        if local:
            output_file = os.path.join(self.local_dir, output_file)
        else:
            output_file = os.path.join(self.uploads_directory, output_file)
        input_xml = pywws.plot.GraphFileReader(input_file)
        if (input_xml.get_children(self.plotter.plot_name) and
                        self.plotter.do_plot(input_xml, output_file) == 0):
            return output_file
        if (input_xml.get_children(self.roseplotter.plot_name) and
                        self.roseplotter.do_plot(input_xml, output_file) == 0):
            return output_file
        logger.warning('nothing to graph in %s', input_file)
        return None

    def do_template(self, template, data=None, local=False):
        logger.info("Templating %s", template)
        input_file = os.path.join(self.template_dir, template)
        if local:
            output_file = os.path.join(self.local_dir, template)
        else:
            output_file = os.path.join(self.uploads_directory, template)
        self.templater.make_file(input_file, output_file, live_data=data)
        return output_file
