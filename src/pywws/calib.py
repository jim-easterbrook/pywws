# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-18  pywws contributors

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

"""
Calibrate raw weather station data

This module allows adjustment of raw data from the weather station as
part of the 'processing' step (see :doc:`pywws.process`). For example,
if you have fitted a funnel to double your rain gauge's collection
area, you can write a calibration routine to double the rain value.

The default calibration generates the relative atmospheric pressure.
Any user calibration you write must also do this.

Writing your calibration module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Firstly, decide where you want to keep your module. Like your text and
graph templates, it's best to keep it separate from the pywws code, so
it isn't affected by pywws upgrades. I suggest creating a ``modules``
directory in the same place as your ``templates`` directory.

You could start by copying one of the example calibration modules, or
you can create a plain text file in your ``modules`` directory, e.g.
``calib.py`` and copy the following text into it:

.. code-block:: python3

    class Calib(object):
        def __init__(self, params, stored_data):
            self.pressure_offset = float(params.get('config', 'pressure offset'))

        def calib(self, raw):
            result = dict(raw)
            # calculate relative pressure
            result['rel_pressure'] = result['abs_pressure'] + self.pressure_offset
            return result

The :class:`Calib` class has two methods. :py:meth:`Calib.__init__` is
the constructor and is a good place to set any constants you need. It
is passed a reference to the raw data storage which can be useful for
advanced tasks such as spike removal. :py:meth:`Calib.calib` generates
a single set of 'calibrated' data from a single set of 'raw' data.
There are a few rules to follow when writing this method:

    - Make sure you include the line ``result = dict(raw)``, which
      copies all the raw data to your result value, at the start.

    - Don't modify any of the raw data.

    - Make sure you set ``result['rel_pressure']``.

    - Don't forget to ``return`` the result at the end.

When you've finished writing your calibration module you can get pywws
to use it by putting its location in your ``weather.ini`` file. It
goes in the ``[paths]`` section, as shown in the example below::

    [paths]
    work = /tmp/weather
    templates = /home/jim/weather/templates/
    graph_templates = /home/jim/weather/graph_templates/
    user_calib = /home/jim/weather/modules/usercalib

Note that the ``user_calib`` value need not include the ``.py`` at the
end of the file name.

"""

__docformat__ = "restructuredtext en"

import importlib
import logging
import os
import sys

logger = logging.getLogger(__name__)


class DefaultCalib(object):
    """Default calibration class.

    This class sets the relative pressure, using a pressure offset
    originally read from the weather station. This is the bare minimum
    'calibration' required.

    """
    def __init__(self, params, stored_data):
        self.pressure_offset = float(params.get('config', 'pressure offset'))

    def calib(self, raw):
        result = dict(raw)
        # calculate relative pressure
        result['rel_pressure'] = result['abs_pressure'] + self.pressure_offset
        return result


usercalib = None


class Calib(object):
    """Calibration class that implements default or user calibration.

    Other pywws modules use this method to create a calibration
    object. The constructor creates either a default calibration
    object or a user calibration object, depending on the
    ``user_calib`` value in the ``[paths]`` section of the ``params``
    parameter. It then adopts the calibration object's
    :py:meth:`calib` method as its own.

    """
    calibrator = None
    def __init__(self, params, stored_data):
        global usercalib
        if not Calib.calibrator:
            user_module = params.get('paths', 'user_calib', None)
            if user_module:
                logger.info('Using user calibration')
                path, module = os.path.split(user_module)
                sys.path.insert(0, path)
                module = os.path.splitext(module)[0]
                usercalib = importlib.import_module(module)
                del sys.path[0]
                Calib.calibrator = usercalib.Calib(params, stored_data)
            else:
                logger.info('Using default calibration')
                Calib.calibrator = DefaultCalib(params, stored_data)
        self.calib = Calib.calibrator.calib
