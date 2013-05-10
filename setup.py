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

from distutils.core import setup
import sys
sys.path.insert(0, 'code')
from pywws.version import version

cmdclass = {}

# if using Python 3, translate during build
try:
    from distutils.command.build_py import build_py_2to3 as build_py
    cmdclass['build_py'] = build_py
except ImportError:
    pass

# if sphinx is installed, add command to build documentation
try:
    from sphinx.setup_command import BuildDoc
    cmdclass['build_sphinx'] = BuildDoc
except ImportError:
    pass

# if Sphinx-PyPI-upload is installed, add command to upload documentation
try:
    from sphinx_pypi_upload import UploadDoc
    cmdclass['upload_sphinx'] = UploadDoc
except ImportError:
    pass

setup(name = 'pywws',
      version = version,
      description = 'Python software for wireless weather stations',
      author = 'Jim Easterbrook',
      author_email = 'jim@jim-easterbrook.me.uk',
      url = 'http://jim-easterbrook.github.com/pywws/',
      long_description = """
A collection of Python scripts to read, store and process data from
popular USB wireless weather stations such as Elecsa AstroTouch 6975,
Watson W-8681, WH-1080PC, WH1080, WH1081, WH3080 etc. I assume any
model that is supplied with the EasyWeather Windows software is
compatible, but cannot guarantee this.

The software has been developed to run in a low power, low memory
environment such as a router. It can be used to create graphs and web
pages showing recent weather readings, typically updated every hour.
""",
      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          ],
      packages = ['pywws'],
      package_dir = {'': 'code'},
      package_data = {
          'pywws' : ['services/*', 'locale/*/LC_MESSAGES/*'],
          },
      cmdclass = cmdclass,
      )
