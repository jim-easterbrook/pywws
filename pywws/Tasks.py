#!/usr/bin/env python

"""Routines to perform common tasks such as plotting gaphs or uploading files."""

import os

from Plot import GraphPlotter
import Template
from WindRose import RosePlotter

def DoPlots(section, params, raw_data, hourly_data, daily_data, monthly_data,
            translation, verbose):
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
        if verbose > 0:
            print "Graphing", template
        output_file = os.path.join(work_dir, os.path.splitext(template)[0])
        if plotter.DoPlot(input_file, output_file) == 0:
            result.append(output_file)
        elif roseplotter.DoPlot(input_file, output_file) == 0:
            result.append(output_file)
    return result
def DoTemplates(section, params, raw_data, hourly_data, daily_data, monthly_data,
                translation, verbose):
    work_dir = params.get('paths', 'work', '/tmp/weather')
    template_dir = params.get(
        'paths', 'templates', os.path.expanduser('~/weather/templates/'))
    templates = eval(params.get(section, 'text', '[]'))
    result = []
    for template in templates:
        input_file = os.path.join(template_dir, template)
        if verbose > 0:
            print "Templating", template
        output_file = os.path.join(work_dir, template)
        Template.Template(
            params, raw_data, hourly_data, daily_data,
            monthly_data, input_file, output_file, translation=translation)
        result.append(output_file)
    return result
def DoTwitter(section, params, raw_data, hourly_data, daily_data, monthly_data,
              translation, verbose):
    import ToTwitter
    work_dir = params.get('paths', 'work', '/tmp/weather')
    template_dir = params.get(
        'paths', 'templates', os.path.expanduser('~/weather/templates/'))
    templates = eval(params.get(section, 'twitter', '[]'))
    for template in templates:
        input_file = os.path.join(template_dir, template)
        if verbose > 0:
            print "Templating", template
        output_file = os.path.join(work_dir, template)
        Template.Template(
            params, raw_data, hourly_data, daily_data,
            monthly_data, input_file, output_file, translation=translation)
        if verbose > 0:
            print "Tweeting"
        # have three tries before giving up
        for n in range(3):
            try:
                ToTwitter.ToTwitter(params, output_file, translation=translation)
                break
            except Exception, ex:
                print >>sys.stderr, ex
        os.unlink(output_file)
