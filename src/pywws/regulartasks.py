# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-21  pywws contributors

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

from ast import literal_eval
from datetime import datetime, timedelta
import importlib
import logging
import os
import sys
import time

from pywws.calib import Calib
import pywws.plot
import pywws.template
from pywws.timezone import time_zone
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
        self.flush = literal_eval(
            self.params.get('config', 'frequent writes', 'False'))
        # get directories
        self.template_dir = self.params.get(
            'paths', 'templates', os.path.expanduser('~/weather/templates/'))
        self.graph_template_dir = self.params.get(
            'paths', 'graph_templates',
            os.path.expanduser('~/weather/graph_templates/'))
        self.module_dir = self.params.get(
            'paths', 'modules', os.path.expanduser('~/weather/modules/'))
        # create calibration object
        self.calibrator = Calib(self.params, self.raw_data)
        # create templater object
        self.templater = pywws.template.Template(context)
        # create plotter objects
        self.plotter = pywws.plot.GraphPlotter(context, self.context.work_dir)
        self.roseplotter = pywws.windrose.RosePlotter(
            context, self.context.work_dir)
        # get daytime end hour
        self.day_end_hour, self.use_dst = pywws.process.get_day_end_hour(
                                                                self.params)
        # parse "cron" sections
        self.cron = {}
        for section in self.params._config.sections():
            if section.split()[0] != 'cron':
                continue
            import croniter
            last_update = self.status.get_datetime('last update', section)
            last_update = last_update or datetime.utcnow()
            self.cron[section] = croniter.croniter(
                self.params.get(section, 'format', ''),
                start_time=time_zone.utc_to_local(last_update))
            self.cron[section].get_next()
        # create service uploader objects
        self.services = {}
        for section in list(self.cron.keys()) + [
                       'live', 'logged', 'hourly', '12 hourly', 'daily']:
            for name, options in self._parse_templates(section, 'services'):
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

    def has_live_tasks(self):
        if self.cron:
            return True
        for name in literal_eval(self.params.get('live', 'services', '[]')):
            return True
        for template in literal_eval(self.params.get('live', 'plot', '[]')):
            return True
        for template in literal_eval(self.params.get('live', 'text', '[]')):
            return True
        return False

    def _parse_templates(self, section, option):
        for template in literal_eval(self.params.get(section, option, '[]')):
            if isinstance(template, (list, tuple)):
                yield template[0], template[1:]
            else:
                yield template, ()

    def _do_common(self, now, sections, live_data=None):
        logger.info('doing task sections {!r}'.format(sections))
        # make lists of tasks from all sections, avoiding repeats
        service_tasks = []
        text_tasks = []
        plot_tasks = []
        for section in sections:
            for task in self._parse_templates(section, 'services'):
                if task not in service_tasks:
                    service_tasks.append(task)
            for task in self._parse_templates(section, 'text'):
                if task not in text_tasks:
                    text_tasks.append(task)
            for task in self._parse_templates(section, 'plot'):
                if task not in plot_tasks:
                    plot_tasks.append(task)
        # do plot templates
        for template, flags in plot_tasks:
            self.do_plot(template)
        # do text templates
        for template, flags in text_tasks:
            self.do_template(template, data=live_data)
        # do service tasks
        for name, options in service_tasks:
            self.services[name].upload(live_data=live_data, options=options)
        # allow all services to sent some catchup records
        catchup = list(self.services.keys())
        stop = time.time() + 20.0
        while catchup and time.time() < stop:
            for name in list(catchup):
                if self.services[name].do_catchup():
                    catchup.remove(name)
        # update status
        for section in sections:
            self.status.set('last update', section, now.isoformat(' '))
        # save any unsaved data
        if self.flush or 'hourly' in sections:
            self.context.flush()

    def _cron_due(self, now):
        if not self.cron:
            return []
        # make list of due sections
        sections = []
        for section in self.cron:
            if time_zone.local_to_utc(
                    self.cron[section].get_current(datetime)) > now:
                continue
            sections.append(section)
            while time_zone.local_to_utc(
                    self.cron[section].get_next(datetime)) <= now:
                pass
        return sections

    def _periodic_due(self, now):
        # make list of due sections
        sections = []
        # hourly
        threshold = time_zone.hour_start(now)
        last_update = self.status.get_datetime('last update', 'hourly')
        if not last_update or last_update < threshold:
            sections.append('hourly')
        # daily
        threshold = time_zone.day_start(
            now, self.day_end_hour, use_dst=self.use_dst)
        last_update = self.status.get_datetime('last update', 'daily')
        if not last_update or last_update < threshold:
            sections.append('daily')
        # 12 hourly
        threshold = max(threshold, time_zone.day_start(
            now, (self.day_end_hour + 12) % 24, use_dst=self.use_dst))
        last_update = self.status.get_datetime('last update', '12 hourly')
        if not last_update or last_update < threshold:
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

    def do_plot(self, template):
        logger.info("Graphing %s", template)
        input_file = os.path.join(self.graph_template_dir, template)
        output_file = os.path.join(
            self.context.output_dir, os.path.splitext(template)[0])
        input_xml = pywws.plot.GraphFileReader(input_file)
        if (input_xml.get_children(self.plotter.plot_name) and
                        self.plotter.do_plot(input_xml, output_file) == 0):
            return output_file
        if (input_xml.get_children(self.roseplotter.plot_name) and
                        self.roseplotter.do_plot(input_xml, output_file) == 0):
            return output_file
        logger.warning('nothing to graph in %s', input_file)
        return None

    def do_template(self, template, data=None):
        logger.info("Templating %s", template)
        input_file = os.path.join(self.template_dir, template)
        output_file = os.path.join(self.context.output_dir, template)
        self.templater.make_file(input_file, output_file, live_data=data)
        return output_file
