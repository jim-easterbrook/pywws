#!/usr/bin/env python

from distutils.core import setup
import sys
sys.path.append('code')
from pywws.version import version

if sys.version_info[0] >= 3:
    code_dir = 'code3'
else:
    code_dir = 'code'

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
      package_dir = {'': code_dir},
      package_data = {
          'pywws' : ['services/*', 'locale/*/LC_MESSAGES/*'],
          },
      scripts = ['%s/Hourly.py' % code_dir, '%s/LiveLog.py' % code_dir],
      )
