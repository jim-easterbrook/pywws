from datetime import timedelta
import logging

from pywws.Process import SECOND

MINUTEx30 = timedelta(minutes=30)

class Calib(object):
    """Weather station calibration class with temperature spike removal."""
    def __init__(self, params, raw_data):
        self.logger = logging.getLogger('pywws.Calib')
        self.raw_data = raw_data
        self.pressure_offset = eval(params.get('config', 'pressure offset'))

    def calib(self, raw):
        result = dict(raw)
        # sanitise data
        if result['wind_dir'] is not None and result['wind_dir'] >= 16:
            result['wind_dir'] = None
        # try to remove spikes in outside temperature
        if result['temp_out'] is not None:
            # get last 30 mins valid temperatures
            history = []
            for data in self.raw_data[result['idx'] - MINUTEx30:
                                      result['idx'] + SECOND]:
                if data['temp_out'] is not None:
                    history.append(data['temp_out'])
            history.sort()
            if len(history) >= 4:
                median = history[(len(history) - 1) / 2]
                if abs(result['temp_out'] - median) > 1.5:
                    self.logger.warning(
                        'spike? %s %s', str(history), str(result['temp_out']))
                if abs(result['temp_out'] - median) > 2.0:
                    result['temp_out'] = None
        # calculate relative pressure
        result['rel_pressure'] = result['abs_pressure'] + self.pressure_offset
        return result
