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

import os
from distutils import log
from distutils.cmd import Command
from distutils.core import setup
import subprocess

import pywws.version

# Custom distutils classes
class build_lang(Command):
    description = '"compile" .po files to .mo files'
    user_options = [
        ('source-dir=', 's', 'root directory of .po source files'),
        ('build-dir=',  'b', 'root directory of .mo output files'),
        ]

    def initialize_options(self):
        self.source_dir = None
        self.build_dir = None

    def finalize_options(self):
        if self.build_dir is None:
            self.build_dir = self.source_dir

    def run(self):
        if not self.source_dir:
            log.error('no source directory specified')
            return
        for root, dirs, files in os.walk(self.source_dir):
            targ_dir = os.path.join(
                root.replace(self.source_dir, self.build_dir), 'LC_MESSAGES')
            for name in files:
                base, ext = os.path.splitext(name)
                if ext.lower() != '.po':
                    continue
                src = os.path.join(root, name)
                targ = os.path.join(targ_dir, base + '.mo')
                if os.path.exists(targ):
                    targ_date = os.stat(targ)[8]
                else:
                    targ_date = 0
                src_date = os.stat(src)[8]
                if targ_date > src_date:
                    log.debug('skipping %s', targ)
                    continue
                if not os.path.isdir(targ_dir):
                    log.info('creating directory %s', targ_dir)
                    if not self.dry_run:
                        os.makedirs(targ_dir)
                log.info('compiling %s to %s', src, targ)
                if not self.dry_run:
                    subprocess.check_call([
                        'msgfmt', '--output-file=%s' % targ, src])

cmdclass = {}
command_options = {}

# if using Python 3, translate during build
try:
    from distutils.command.build_py import build_py_2to3 as build_py
    cmdclass['build_py'] = build_py
except ImportError:
    pass

if 'LANG' in os.environ:
    lang = os.environ['LANG'].split('_')[0]
else:
    lang = 'en'

# add command to build translation files
cmdclass['build_lang'] = build_lang
command_options['build_lang'] = {
    'source_dir' : ('setup.py', 'translations'),
    'build_dir'  : ('setup.py', 'translations'),
    }

# if sphinx is installed, add command to build documentation
try:
    from sphinx.setup_command import BuildDoc
    builder = 'html'
    cmdclass['build_sphinx'] = BuildDoc
    command_options['build_sphinx'] = {
        'all_files'  : ('setup.py', '1'),
        'source_dir' : ('setup.py', 'doc_src'),
        'build_dir'  : ('setup.py', 'doc/%s/%s' % (builder, lang)),
        'builder'    : ('setup.py', builder),
        }
except ImportError:
    pass

# if Sphinx-PyPI-upload is installed, add command to upload documentation
try:
    from sphinx_pypi_upload import UploadDoc
    cmdclass['upload_sphinx'] = UploadDoc
    command_options['upload_sphinx'] = {
        'upload_dir' : ('setup.py', 'doc/html'),
        }
except ImportError:
    pass

# get lists of data files and scripts to install
scripts = []
for name in os.listdir('scripts'):
    scripts.append(os.path.join('scripts', name))
data_files = []
for root, dirs, files in os.walk('examples'):
    paths = []
    for name in files:
        paths.append(os.path.join(root, name))
    if paths:
        data_files.append(('share/pywws/%s' % root, paths))

# PyPI gets confused by git commit identifiers not being in sequence,
# so add a 'minor' version number which will increase if there's a
# second release (or third...) in the month
version = '%s.0.%s' % (pywws.version.version, pywws.version.commit)

setup(name = 'pywws',
      version = version,
      description = 'Python software for wireless weather stations',
      author = 'Jim Easterbrook',
      author_email = 'jim@jim-easterbrook.me.uk',
      url = 'http://jim-easterbrook.github.com/pywws/',
      download_url = 'https://pypi.python.org/pypi/pywws/%s' % version,
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
      license = 'GNU GPL',
      platforms = ['POSIX', 'MacOS', 'Windows'],
      packages = ['pywws'],
      package_data = {
          'pywws' : ['services/*', 'locale/*/LC_MESSAGES/*'],
          },
      scripts = scripts,
      data_files = data_files,
      cmdclass = cmdclass,
      command_options = command_options,
      )
