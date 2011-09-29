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
        # sanitise data
        if result['wind_dir'] is not None and result['wind_dir'] >= 16:
            result['wind_dir'] = None
        # calculate relative pressure
        result['rel_pressure'] = raw['abs_pressure'] + self.pressure_offset
        return result

usercalib = None

class Calib(object):
    def __init__(self, params):
        global usercalib
        self.logger = logging.getLogger('pywws.Calib')
        user_module = params.get('paths', 'user_calib', None)
        if user_module:
            self.logger.info('Using user calibration')
            if not usercalib:
              path, module = os.path.split(user_module)
              sys.path.insert(0, path)
              module = os.path.splitext(module)[0]
              usercalib = __import__(module, globals(), locals(), ['Calib'], -1)
            self.calibrator = usercalib.Calib(params)
        else:
            self.logger.info('Using default calibration')
            self.calibrator = DefaultCalib(params)
        self.calib = self.calibrator.calib
