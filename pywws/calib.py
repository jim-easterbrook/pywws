"""Calibrate raw weather station data."""

from datetime import datetime, timedelta
import logging
import os
import sys

class DefaultCalib(object):
    """Default calibration class - relative pressure conversion only."""
    def __init__(self, params):
        self.pressure_offset = eval(params.get('fixed', 'pressure offset'))
    def calib(self, raw):
        result = dict(raw)
        result['rel_pressure'] = raw['abs_pressure'] + self.pressure_offset
        return result

class Calib(object):
    def __init__(self, params):
        self.logger = logging.getLogger('pywws.Calib')
        user_module = params.get('paths', 'user_calib', None)
        if user_module:
            self.logger.warning('Using user calibration')
            path, module = os.path.split(user_module)
            sys.path.insert(0, path)
            module = os.path.splitext(module)[0]
            temp = __import__(module, globals(), locals(), ['Calib'], -1)
            self.calibrator = temp.Calib(params)
        else:
            self.logger.warning('Using default calibration')
            self.calibrator = DefaultCalib(params)
        self.calib = self.calibrator.calib
