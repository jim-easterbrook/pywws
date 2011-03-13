#!/usr/bin/env python

from distutils.core import setup
from pywws.version import version

setup(name='pywws',
      version=version,
      description='Python software for wireless weather stations',
      author='Jim Easterbrook',
      author_email='jim@jim-easterbrook.me.uk',
      url='http://code.google.com/p/pywws/',
      packages=['pywws'],
      )
