#!/usr/bin/env python

"""Post weather update to the UK Met Office 'WOW' site
::

%s

Introduction
------------

The UK Met Office has recently introduced `WOW - Weather Observations
Website <http://wow.metoffice.gov.uk/>`_. This can accept readings
from automatic weather statons, in a very similar way to `Weather
Underground <http://www.wunderground.com/>`_. This module enables
pywws to upload readings to WOW.

Configuration
-------------

If you haven't already done so, visit the Met Office WOW web site and
create a user account for yourself. Then go to the `'Sites' page
<http://wow.metoffice.gov.uk/sites>`_ and follow the 'create new site'
link. Fill in all the required details, including the 'AWS 6-digit
PIN'. Note that the 'reporting hours' should be set to option C,
regardless of your 'day end hour' setting.

Copy your 'site ID' and 'AWS PIN' from the Met Office web site to a
new ``[metoffice]`` section in your ``weather.ini`` configuration
file::

    [metoffice]
    site id = 12345678
    aws pin = 654321

Remember to stop all pywws software before editing ``weather.ini``.

Test your configuration by running ``ToMetOffice.py`` (replace
``data_dir`` with your weather data directory)::

    python pywws/ToMetOffice.py -vvv data_dir

This should show you the data string that is uploaded, and no other
messages.

Upload old data
---------------

Now you can upload your last 7 days' data. Edit your ``weather.ini``
file and remove the ``last update`` line from the ``[metoffice]``
section, then run ``ToMetOffice.py`` with the catchup option::

    python pywws/ToMetOffice.py -c -v data_dir

This may take 20 minutes or more, depending on how much data you have.

Add Met Office upload to regular tasks
--------------------------------------

Edit your ``weather.ini`` again, and add ``metoffice = True`` to the
``[logged]``, ``[hourly]``, ``[12 hourly]`` or ``[daily]`` section,
depending on how often you want to send data. For example::

    [logged]
    plot = []
    text = []
    twitter = []
    underground = False
    metoffice = True

Restart your regular pywws program (``Hourly.py`` or ``LiveLog.py``)
and visit the Met Office WOW web site to see regular updates from your
weather station.

Acknowledgment
--------------

Thanks to `Tom <mailto:e_l_p_i_s@yahoo.co.uk>`_ for writing the
initial version of ``ToMetOffice.py``.

"""

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: python ToMetOffice.py [options] data_dir
 options are:
  -h or --help     display this help
  -c or --catchup  upload all data since last upload (up to 1 week)
  -v or --verbose  increase amount of reassuring messages
 data_dir is the root directory of the weather data
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import sys

import DataStore
from Logger import ApplicationLogger
import toservice

class ToMetOffice(toservice.ToService):
    """Upload weather data to UK Met Office 'WOW'.

    """
    def __init__(self, params, calib_data):
        """

        :param params: pywws configuration.

        :type params: :class:`pywws.DataStore.params`
        
        :param calib_data: 'calibrated' data.

        :type calib_data: :class:`pywws.DataStore.calib_store`
    
        """
        self.config_section = 'metoffice'
        toservice.ToService.__init__(self, params, calib_data)
        # UK Met Office 'WOW' server
        self.server = 'http://wow.metoffice.gov.uk/automaticreading'
        # set fixed part of upload data
        siteid = self.params.get(self.config_section, 'site id')
        siteAuthenticationKey = self.params.get(self.config_section, 'aws pin')
        self.fixed_data = {
            'siteid'                : siteid,
            'siteAuthenticationKey' : siteAuthenticationKey,
            'softwaretype'          : 'pywws'
            }

    def Upload(self, catchup):
        """Upload one or more weather data records.

        This method uploads either the most recent weather data
        record, or all records since the last upload (up to 7 days),
        according to the value of :obj:`catchup`.

        It sets the ``last update`` configuration value to the time
        stamp of the most recent record successfully uploaded.

        :param catchup: upload all data since last upload.

        :type catchup: bool

        :return: success status

        :rtype: bool
        
        """
        return self.upload(self.server, self.fixed_data, catchup)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hcv", ['help', 'catchup', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    catchup = False
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __usage__.strip()
            return 0
        elif o == '-c' or o == '--catchup':
            catchup = True
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, "Error: 1 argument required"
        print >>sys.stderr, __usage__.strip()
        return 2
    logger = ApplicationLogger(verbose)
    return ToMetOffice(
        DataStore.params(args[0]), DataStore.calib_store(args[0])
        ).Upload(catchup)

if __name__ == "__main__":
    sys.exit(main())
