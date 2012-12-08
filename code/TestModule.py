#!/usr/bin/env python

"""Test a pywws module.

Many of the modules in the pywws package include a simple test script
that is run when that module is run as a script. Unfortunately Python
3 does not allow package modules to be run as scripts, producing a
'ValueError: Attempted relative import in non-package' error. This
script allows module test scripts to be run. ::

%s
"""

__usage__ = """
 usage: python TestModule.py module [module_options]
 module is a pywws module, e.g. ZambrettiCore
 module_options are any options to be passed to the module's test script
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
