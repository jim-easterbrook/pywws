#!/usr/bin/env python

from datetime import date
from distutils.core import setup
from subprocess import Popen, PIPE

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
      )
