#!/usr/bin/env python

from datetime import date
from distutils.command.build import build
from distutils.core import setup, Command
from distutils import log
import os
from subprocess import check_call, Popen, PIPE
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

revision = 0
for line in Popen(['svn', 'info'], stdout=PIPE).stdout:
    if line.startswith('Revision'):
        revision = int(line.split(':')[1])
        break
version = date.today().strftime('%y.%m') + '_r%d' % revision

setup(name='pywws',
      version=version,
      description='Python software for wireless weather stations',
      author='Jim Easterbrook',
      author_email='jim@jim-easterbrook.me.uk',
      url='http://code.google.com/p/pywws/',
      cmdclass={'build_langs': build_langs},
      )
