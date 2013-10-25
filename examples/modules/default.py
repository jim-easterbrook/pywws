class Calib(object):
    """Minimum weather station calibration class."""
    def __init__(self, params, raw_data):
        self.pressure_offset = eval(params.get('config', 'pressure offset'))

    def calib(self, raw):
        result = dict(raw)
        # sanitise data
        if result['wind_dir'] is not None and result['wind_dir'] >= 16:
            result['wind_dir'] = None
        # calculate relative pressure
        result['rel_pressure'] = result['abs_pressure'] + self.pressure_offset
        return result
