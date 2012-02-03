#!/usr/bin/env python

"""Post weather update to WeatherUnderground
::

%s

Introduction
------------

`Weather Underground <http://www.wunderground.com/>`_ is a USA based
web site that gathers weather data from stations around the world.
This module enables pywws to upload readings to Weather Underground.

Configuration
-------------

If you haven't already done so, visit the Weather Underground web site
and create a member account for yourself. Then go to the `'Personal
Weather Stations' page
<http://www.wunderground.com/wxstation/signup.html>`_ and follow the
'new weather station' link. Fill in all the required details, then
click on 'submit'.

Copy your 'station ID' and password to a new ``[underground]`` section
in your ``weather.ini`` configuration file::

    [underground]
    password = secret
    station = ABCDEFG1A

Remember to stop all pywws software before editing ``weather.ini``.

Test your configuration by running ``ToUnderground.py`` (replace
``data_dir`` with your weather data directory)::

    python pywws/ToUnderground.py -vvv data_dir

This should show you the data string that is uploaded and then a
'success' message.

Upload old data
---------------

Now you can upload your last 7 days' data. Edit your ``weather.ini``
file and remove the ``last update`` line from the ``[underground]``
section, then run ``ToUnderground.py`` with the catchup option::

    python pywws/ToUnderground.py -c -v data_dir

This may take 20 minutes or more, depending on how much data you have.

Add Weather Underground upload to regular tasks
-----------------------------------------------

Edit your ``weather.ini`` again, and add ``underground = True`` to the
``[live]``, ``[logged]``, ``[hourly]``, ``[12 hourly]`` or ``[daily]``
section, depending on how often you want to send data. For example::

    [live]
    underground = True
    twitter = []
    plot = []
    text = []

If you set ``underground = True`` in the ``live`` section, pywws will
use Weather Underground's 'Rapid Fire' mode to send a reading every 48
seconds.

Restart your regular pywws program (``Hourly.py`` or ``LiveLog.py``)
and visit the Weather Underground web site to see regular updates from
your weather station.

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python ToUnderground.py [options] data_dir
 options are:
  -h or --help     display this help
  -c or --catchup  upload all data since last upload (up to 4 weeks)
  -v or --verbose  increase amount of reassuring messages
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import sys
from datetime import datetime, timedelta

import DataStore
from Logger import ApplicationLogger
import toservice

FIVE_MINS = timedelta(minutes=5)

class ToUnderground(toservice.ToService):
    """Upload weather data to Weather Underground.

    """
    def __init__(self, params, calib_data):
        """

        :param params: pywws configuration.

        :type params: :class:`pywws.DataStore.params`
        
        :param calib_data: 'calibrated' data.

        :type calib_data: :class:`pywws.DataStore.calib_store`
    
        """
        self.config_section = 'underground'
        toservice.ToService.__init__(self, params, calib_data)
        # Weather Underground server, normal and rapid fire
        self.server = 'http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
        self.server_rf = 'http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php'
        # set fixed part of upload data, versions for normal and rapid fire
        password = self.params.get(
            self.config_section, 'password', 'undergroudpassword')
        station = self.params.get(
            self.config_section, 'station', 'undergroundstation')
        self.fixed_data = {
            'action'       : 'updateraw',
            'ID'           : station,
            'PASSWORD'     : password,
            'softwaretype' : 'pywws',
            }
        self.fixed_data_rf = dict(self.fixed_data)
        self.fixed_data_rf['realtime'] = '1'
        self.fixed_data_rf['rtfreq'] = '48'

    def translate_data(self, current, fixed_data):
        """Convert a weather data record to upload format.

        The :obj:`current` parameter contains the data to be uploaded.
        It should be a 'calibrated' data record, as stored in
        :class:`pywws.DataStore.calib_store`.

        The :obj:`fixed_data` parameter contains unvarying data that
        is site dependent, for example an ID code and authentication
        data.

        :param current: the weather data record.

        :type current: dict

        :param fixed_data: unvarying upload data.

        :type fixed_data: dict

        :return: converted data, or :obj:`None` if invalid data.

        :rtype: dict(string)
        
        """
        result = toservice.ToService.translate_data(self, current, fixed_data)
        if result and current.has_key('uv'):
            if current['uv'] is not None:
                result['UV'] = '%d' % (current['uv'])
            if current['illuminance'] is not None:
                # approximate conversion from lux to W/m2
                result['solarradiation'] = '%.2f' % (
                    current['illuminance'] * 0.005)
        return result

    def RapidFire(self, data, catchup):
        """Upload a 'Rapid Fire' weather data record.

        This method uploads either a single data record (typically one
        obtained during 'live' logging), or all records since the last
        upload (up to 7 days), according to the value of
        :obj:`catchup`.

        It sets the ``last update`` configuration value to the time
        stamp of the most recent record successfully uploaded.

        The :obj:`data` parameter contains the data to be uploaded.
        It should be a 'calibrated' data record, as stored in
        :class:`pywws.DataStore.calib_store`.

        :param data: the weather data record.

        :type data: dict

        :param catchup: upload all data since last upload.

        :type catchup: bool

        :return: success status

        :rtype: bool
        
        """
        last_log = self.data.before(datetime.max)
        if not last_log or last_log < data['idx'] - FIVE_MINS:
            # logged data is not (yet) up to date
            return True
        if catchup:
            last_update = self.params.get_datetime(
                self.config_section, 'last update')
            if not last_update:
                last_update = datetime.min
            if last_update <= last_log - FIVE_MINS:
                # last update was well before last logged data
                if not self.Upload(True):
                    return False
        if not self.send_data(data, self.server_rf, self.fixed_data_rf):
            return False
        self.params.set(
            self.config_section, 'last update', data['idx'].isoformat(' '))
        return True

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hcv", ['help', 'catchup', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    catchup = False
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
        elif o == '-c' or o == '--catchup':
            catchup = True
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, "Error: 1 argument required"
        print >>sys.stderr, __doc__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    return ToUnderground(
        DataStore.params(args[0]), DataStore.calib_store(args[0])
        ).Upload(catchup)

if __name__ == "__main__":
    sys.exit(main())
