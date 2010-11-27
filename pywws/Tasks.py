#!/usr/bin/env python

"""Routines to perform common tasks such as plotting gaphs or uploading files."""

from datetime import datetime, timedelta
import logging
import os

from Plot import GraphPlotter
import Template
from TimeZone import Local, utc
import ToUnderground
import Upload
from WindRose import RosePlotter

def DoPlots(section, params, raw_data, hourly_data, daily_data, monthly_data,
            translation):
    logger = logging.getLogger('pywws.Tasks.DoPlots')
    work_dir = params.get('paths', 'work', '/tmp/weather')
    plotter = GraphPlotter(
        params, raw_data, hourly_data, daily_data, monthly_data, work_dir,
        translation=translation)
    roseplotter = RosePlotter(
        params, raw_data, hourly_data, daily_data, monthly_data, work_dir,
        translation=translation)
    graph_template_dir = params.get(
        'paths', 'graph_templates', os.path.expanduser('~/weather/graph_templates/'))
    templates = eval(params.get(section, 'plot', '[]'))
    result = []
    for template in templates:
        input_file = os.path.join(graph_template_dir, template)
        logger.info("Graphing %s", template)
        output_file = os.path.join(work_dir, os.path.splitext(template)[0])
        if plotter.DoPlot(input_file, output_file) == 0:
            result.append(output_file)
        elif roseplotter.DoPlot(input_file, output_file) == 0:
            result.append(output_file)
    return result
def DoTemplates(section, params, raw_data, hourly_data, daily_data, monthly_data,
                translation):
    logger = logging.getLogger('pywws.Tasks.DoTemplates')
    work_dir = params.get('paths', 'work', '/tmp/weather')
    template_dir = params.get(
        'paths', 'templates', os.path.expanduser('~/weather/templates/'))
    templates = eval(params.get(section, 'text', '[]'))
    result = []
    for template in templates:
        input_file = os.path.join(template_dir, template)
        logger.info("Templating %s", template)
        output_file = os.path.join(work_dir, template)
        Template.Template(
            params, raw_data, hourly_data, daily_data,
            monthly_data, input_file, output_file, translation=translation)
        result.append(output_file)
    return result
def DoTwitter(section, params, raw_data, hourly_data, daily_data, monthly_data,
              translation):
    logger = logging.getLogger('pywws.Tasks.DoTwitter')
    work_dir = params.get('paths', 'work', '/tmp/weather')
    template_dir = params.get(
        'paths', 'templates', os.path.expanduser('~/weather/templates/'))
    templates = eval(params.get(section, 'twitter', '[]'))
    if not templates:
        return True
    import ToTwitter
    twitter = ToTwitter.ToTwitter(params, translation=translation)
    for template in templates:
        input_file = os.path.join(template_dir, template)
        logger.info("Templating %s", template)
        tweet = Template.TemplateText(
            params, raw_data, hourly_data, daily_data,
            monthly_data, input_file, translation)
        logger.info("Tweeting")
        if not twitter.Upload(tweet[:140]):
            return False
    return True
class RegularTasks(object):
    def __init__(self, params, raw_data, hourly_data, daily_data, monthly_data,
                 translation):
        self.params = params
        self.raw_data = raw_data
        self.hourly_data = hourly_data
        self.daily_data = daily_data
        self.monthly_data = monthly_data
        self.translation = translation
        # create a ToUnderground object
        self.underground = ToUnderground.ToUnderground(self.params, self.raw_data)
        # get local time's offset from UTC, without DST
        now = self.raw_data.before(datetime.max)
        time_offset = Local.utcoffset(now) - Local.dst(now)
        # get daytime end hour, in UTC
        self.day_end_hour = eval(params.get('config', 'day end hour', '21'))
        self.day_end_hour = (self.day_end_hour - (time_offset.seconds / 3600)) % 24
    def do_tasks(self):
        sections = ['live']
        now = self.raw_data.before(datetime.max)
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
        uploads = []
        OK = True
        for section in sections:
            if not DoTwitter(
                section, self.params, self.raw_data, self.hourly_data,
                self.daily_data, self.monthly_data, self.translation):
                OK = False
                break
            if eval(self.params.get(section, 'underground', 'False')):
                if not self.underground.Upload(True):
                    OK = False
                    break
            uploads += DoPlots(
                section, self.params, self.raw_data, self.hourly_data,
                self.daily_data, self.monthly_data, self.translation)
            uploads += DoTemplates(
                section, self.params, self.raw_data, self.hourly_data,
                self.daily_data, self.monthly_data, self.translation)
        if uploads:
            OK = OK and Upload.Upload(self.params, uploads) == 0
            for file in uploads:
                os.unlink(file)
        if OK:
            for section in sections:
                self.params.set(section, 'last update', now.isoformat(' '))
        return OK
