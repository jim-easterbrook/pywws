#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

"""Run a pywws module.

Many of the modules in the pywws package include a 'main' function
that is run when that module is run as a script. Unfortunately running
package modules as scripts has been deprecated, producing a
'ValueError: Attempted relative import in non-package' error. This
program allows pywws module scripts to be run. ::

%s
"""

__usage__ = """
 usage: python RunModule.py module [module_options]
 module is a pywws module, e.g. ZambrettiCore
 module_options are options and parameters to be passed to the module
"""
__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import sys

def main(argv=None):
    if argv is None:
        argv = sys.argv
    # check arguments
    if len(argv) < 2:
        print >>sys.stderr, 'Error: no module specified\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    # do it!
    module = __import__('pywws.%s' % argv[1], globals(), locals(), ['main'], -1)
    return module.main(argv=argv[1:])

if __name__ == "__main__":
    sys.exit(main())
