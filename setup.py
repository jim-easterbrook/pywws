#!/usr/bin/env python

from distutils.command.build import build
from distutils.core import setup, Command
from distutils import log
import os
from subprocess import check_call
import sys
if sys.platform == 'win32':
    sys.path.append(os.path.join(sys.prefix, 'Tools', 'i18n'))
    import msgfmt

class build_langs(Command):
    description = 'Compile language localisation files.'
    user_options = []
    def initialize_options(self):
    	pass
    def finalize_options(self):
    	pass
    def run(self):
        # compile language files
        srcDir = os.path.join(os.path.dirname(sys.argv[0]), 'languages')
        langRoot = os.path.join(os.path.dirname(sys.argv[0]), 'locale')
        for file in os.listdir(srcDir):
            base, ext = os.path.splitext(file)
            if ext.lower() != '.po':
                continue
            src = os.path.join(srcDir, file)
            dest = os.path.join(langRoot, base, 'LC_MESSAGES', 'pywws.mo')
            if os.path.exists(dest) and os.path.getctime(dest) > os.path.getctime(src):
                continue
            log.info("Creating %s" % (dest))
            dest_dir = os.path.dirname(dest)
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)
            if sys.platform == 'win32':
                msgfmt.make(src, dest)
            else:
                check_call(['msgfmt', '--output-file=%s' % dest, src])
build.sub_commands.insert(0, ('build_langs', None))

setup(name='pywws',
      version='10.02',
      description='Python software for wireless weather stations',
      author='Jim Easterbrook',
      author_email='jim@jim-easterbrook.me.uk',
      url='http://code.google.com/p/pywws/',
      cmdclass={'build_langs': build_langs},
      )
