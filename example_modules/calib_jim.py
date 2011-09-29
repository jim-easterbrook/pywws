from datetime import datetime

class Calib(object):
    """Jim's weather station calibration class."""
    def __init__(self, params):
        # pressure sensor went wrong on 19th August 2011
        self.pressure_fault = datetime(2011, 8, 19, 11, 0, 0)

    def calib(self, raw):
        result = dict(raw)
        # sanitise data
        if result['wind_dir'] is not None and result['wind_dir'] >= 16:
            result['wind_dir'] = None
        # pressure readings are nonsense since sensor failed
        if raw['idx'] < self.pressure_fault:
            result['rel_pressure'] = raw['abs_pressure'] + 7.4
        else:
            result['abs_pressure'] = None
            result['rel_pressure'] = None
        return result
