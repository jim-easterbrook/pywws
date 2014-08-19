# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-14  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

"""Display pywws version information.

This script can also be run with the ``pywws-version`` command. ::
%s

"""

from __future__ import absolute_import

__docformat__ = "restructuredtext en"
__usage__ = """
 usage: %s [options]
 options are:
  -h      or --help      display this help
  -v      or --verbose   show verbose version information
"""
__doc__ %= __usage__ % ('python -m pywws.version')

import getopt
import os
from pkg_resources import resource_filename
import sys

from . import __version__, _commit

def main(argv=None):
    if argv is None:
        argv = sys.argv
    usage = (__usage__ % (argv[0])).strip()
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, usage
        return 1
    # process options
    verbose = False
    for o, a in opts:
        if o in ('-h', '--help'):
            print __doc__.split('\n\n')[0]
            print usage
            return 0
        elif o in ('-v', '--verbose'):
            verbose = True
    # check arguments
    if len(args) != 0:
        print >>sys.stderr, 'Error: no arguments permitted\n'
        print >>sys.stderr, usage
        return 2
    print __version__
    if verbose:
        print 'commit:', _commit
        print 'Python:', sys.version
        try:
            from .WeatherStation import USBDevice
            print 'USB:   ', USBDevice.__module__
        except ImportError:
            print 'USB:    missing'
        example_dir = resource_filename('pywws', 'examples')
        if os.path.exists(example_dir):
            print 'examples:'
            print '  ', example_dir
        print 'docs:'
        print '   http://jim-easterbrook.github.com/pywws/'
    return 0

if __name__ == '__main__':
    sys.exit(main())
