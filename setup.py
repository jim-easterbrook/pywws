#!/usr/bin/env python

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

from datetime import date
from distutils import log
import os
from setuptools import setup
import subprocess

# read current version info without importing pywws package
with open('pywws/__init__.py') as f:
    exec(f.read())

# regenerate version info, if required
regenerate = False
try:
    p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commit = p.communicate()[0].strip().decode('ASCII')
    regenerate = (not p.returncode) and commit != _commit
except OSError:
    pass
if regenerate:
    release = str(int(_release) + 1)
    version = date.today().strftime('%y.%m') + '.dev%s' % release
    vf = open('pywws/__init__.py', 'w')
    vf.write("""__version__ = '%s'
_release = '%s'
_commit = '%s'
""" % (version, release, commit))
    vf.close()
else:
    version = __version__

cmdclass = {}
command_options = {}

if 'LANG' in os.environ:
    lang = os.environ['LANG'].split('_')[0]
else:
    lang = 'en'

# add commands to create & build translation files
# requires Babel to be installed
command_options['compile_catalog'] = {
    'domain'    : ('setup.py', 'pywws'),
    'directory' : ('setup.py', 'pywws/lang'),
    'use_fuzzy' : ('setup.py', '1'),
    }
command_options['extract_messages'] = {
    'input_dirs'         : ('setup.py', 'pywws'),
    'output_file'        : ('setup.py', 'build/gettext/pywws.pot'),
    'no_wrap'            : ('setup.py', '1'),
    'sort_by_file'       : ('setup.py', '1'),
    'add_comments'       : ('setup.py', 'TX_NOTE'),
    'strip_comments'     : ('setup.py', '1'),
    'copyright_holder'   : ('setup.py', 'Jim Easterbrook'),
    'msgid_bugs_address' : ('setup.py', 'jim@jim-easterbrook.me.uk'),
    }
command_options['init_catalog'] = {
    'domain'     : ('setup.py', 'pywws'),
    'input_file' : ('setup.py', 'build/gettext/pywws.pot'),
    'output_dir' : ('setup.py', 'pywws/lang'),
    'no_wrap'    : ('setup.py', '1'),
    }
command_options['update_catalog'] = {
    'domain'     : ('setup.py', 'pywws'),
    'input_file' : ('setup.py', 'build/gettext/pywws.pot'),
    'output_dir' : ('setup.py', 'pywws/lang'),
    'no_wrap'    : ('setup.py', '1'),
    }

# if sphinx is installed, add commands to build documentation
try:
    from sphinx.setup_command import BuildDoc
    # compile documentation to html
    cmdclass['build_sphinx'] = BuildDoc
    command_options['build_sphinx'] = {
        'source_dir' : ('setup.py', 'doc_src'),
        'build_dir'  : ('setup.py', 'pywws/doc/%s' % (lang)),
        'builder'    : ('setup.py', 'html'),
        }
    # extract strings for translation
    class extract_messages_doc(BuildDoc):
        description = 'extract localizable strings from the documentation'
    cmdclass['extract_messages_doc'] = extract_messages_doc
    command_options['extract_messages_doc'] = {
        'source_dir' : ('setup.py', 'doc_src'),
        'build_dir'  : ('setup.py', 'build'),
        'builder'    : ('setup.py', 'gettext'),
        }
except ImportError:
    pass

# set options for uploading documentation to PyPI
command_options['upload_docs'] = {
    'upload_dir' : ('setup.py', 'pywws/doc'),
    }

# set options for building distributions
command_options['sdist'] = {
    'formats'        : ('setup.py', 'gztar zip'),
    }

with open('README.rst') as ldf:
    long_description = ldf.read()

setup(name = 'pywws',
      version = version,
      description = 'Python software for wireless weather stations',
      author = 'Jim Easterbrook',
      author_email = 'jim@jim-easterbrook.me.uk',
      url = 'http://jim-easterbrook.github.com/pywws/',
      download_url = 'https://pypi.python.org/pypi/pywws/%s' % version,
      long_description = long_description,
      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          ],
      license = 'GNU GPL',
      platforms = ['POSIX', 'MacOS', 'Windows'],
      packages = ['pywws'],
      package_data = {
          'pywws' : [
              'services/*',
              'lang/*/LC_MESSAGES/pywws.mo',
              'doc/*.*', 'doc/*/html/*.*', 'doc/*/html/*/*.*', 'doc/*/html/*/*/*',
              'examples/*/*.*', 'examples/*/*/*.*',
              ],
          },
      cmdclass = cmdclass,
      command_options = command_options,
      entry_points = {
          'console_scripts' : [
              'pywws-hourly             = pywws.Hourly:main',
              'pywws-livelog            = pywws.LiveLog:main',
              'pywws-livelog-daemon     = pywws.livelogdaemon:main',
              'pywws-reprocess          = pywws.Reprocess:main',
              'pywws-setweatherstation  = pywws.SetWeatherStation:main',
              'pywws-testweatherstation = pywws.TestWeatherStation:main',
              'pywws-version            = pywws.version:main',
              ],
          },
      extras_require = {
          'daemon'  : ['python-daemon'],
          'sftp'    : ['paramiko', 'pycrypto'],
          'twitter' : ['python-twitter >= 1.0', 'oauth2'],
          },
      zip_safe = False,
      use_2to3 = True,
      )
