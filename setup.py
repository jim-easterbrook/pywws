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

from datetime import date
from distutils import log
from distutils.cmd import Command
try:
    from setuptools import setup
    using_setuptools = True
except ImportError:
    from distutils.core import setup
    using_setuptools = False
import os
import subprocess

import pywws.version

# regenerate version file, if required
regenerate = False
try:
    p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commit = p.communicate()[0].strip().decode('ASCII')
    regenerate = (not p.returncode) and commit != pywws.version.commit
except OSError:
    pass
if regenerate:
    release = str(int(pywws.version.release) + 1)
    version = date.today().strftime('%y.%m') + '.dev%s' % release
    vf = open('pywws/version.py', 'w')
    vf.write("""version = '%s'
release = '%s'
commit = '%s'
if __name__ == '__main__':
    print(version)
""" % (version, release, commit))
    vf.close()
else:
    version = pywws.version.version

# Custom distutils classes
class xgettext(Command):
    description = 'extract strings for translation from Python source'
    user_options = [
        ('source-dir=', 's', 'root directory of .py source files'),
        ('output-file=',  'o', '.pot output file'),
        ]

    def initialize_options(self):
        self.source_dir = None
        self.output_file = None

    def finalize_options(self):
        pass

    def run(self):
        if not self.source_dir:
            log.error('no source directory specified')
            return
        if not self.output_file:
            log.error('no output file specified')
            return
        src_list = []
        for root, dirs, files in os.walk(self.source_dir):
            for name in files:
                base, ext = os.path.splitext(name)
                if ext.lower() != '.py':
                    continue
                src = os.path.join(root, name)
                src_list.append(src)
        if not src_list:
            log.error('no python files found')
            return
        options = [
            '--language=Python', '--no-wrap',
            '--copyright-holder="Jim Easterbrook"', '--package-name=pywws',
            '--package-version=%s' % version,
            '--msgid-bugs-address="jim@jim-easterbrook.me.uk"',
            '--output=%s' % self.output_file,
            ]
        self.mkpath(os.path.dirname(self.output_file))
        log.info('generating %s', self.output_file)
        if not self.dry_run:
            subprocess.check_call(['xgettext'] + options + src_list)

class msgmerge(Command):
    description = 'merge extracted strings for translation'
    user_options = [
        ('source-dir=', 's', 'root directory of .pot source files'),
        ('build-dir=',  'b', 'root directory of .po output files'),
        ('lang=',       'l', 'language code'),
        ]

    def initialize_options(self):
        self.source_dir = None
        self.build_dir = None
        self.lang = None

    def finalize_options(self):
        if self.build_dir is None:
            self.build_dir = self.source_dir

    def run(self):
        if not self.source_dir:
            log.error('no source directory specified')
            return
        if not self.lang:
            log.error('no language code specified')
            return
        build_dir = os.path.join(self.build_dir, self.lang)
        self.mkpath(build_dir)
        for name in os.listdir(self.source_dir):
            base, ext = os.path.splitext(name)
            if ext.lower() != '.pot':
                continue
            src = os.path.join(self.source_dir, name)
            dest = os.path.join(build_dir, name[:-1])
            if os.path.exists(dest):
                command = 'msgmerge'
                options = ['--no-wrap', '--update', dest, src]
            else:
                command = 'msginit'
                options = [
                    '--no-wrap', '--locale=%s' % self.lang,
                    '--input=%s' % src, '--output-file=%s' % dest]
            log.info('generating %s', dest)
            if not self.dry_run:
                subprocess.check_call([command] + options)

class msgfmt(Command):
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
                self.mkpath(targ_dir)
                log.info('compiling %s to %s', src, targ)
                if not self.dry_run:
                    subprocess.check_call(
                        ['msgfmt', '--use-fuzzy',
                         '--output-file=%s' % targ, src])

cmdclass = {}
command_options = {}
setup_kw = {}

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

# add commands to create & build translation files
cmdclass['xgettext'] = xgettext
command_options['xgettext'] = {
    'source_dir'  : ('setup.py', 'pywws'),
    'output_file' : ('setup.py', 'build/gettext/pywws.pot'),
    }
cmdclass['msgmerge'] = msgmerge
command_options['msgmerge'] = {
    'source_dir' : ('setup.py', 'build/gettext'),
    'build_dir'  : ('setup.py', 'translations'),
    'lang'       : ('setup.py', lang),
    }
cmdclass['msgfmt'] = msgfmt
command_options['msgfmt'] = {
    'source_dir' : ('setup.py', 'translations'),
    'build_dir'  : ('setup.py', 'pywws/lang'),
    }

# if sphinx is installed, add commands to build documentation
try:
    from sphinx.setup_command import BuildDoc
    # compile documentation to html
    builder = 'html'
    cmdclass['build_sphinx'] = BuildDoc
    command_options['build_sphinx'] = {
        'source_dir' : ('setup.py', 'doc_src'),
        'build_dir'  : ('setup.py', 'doc/%s/%s' % (builder, lang)),
        'builder'    : ('setup.py', builder),
        }
    # extract strings for translation
    cmdclass['xgettext_doc'] = BuildDoc
    command_options['xgettext_doc'] = {
        'source_dir' : ('setup.py', 'doc_src'),
        'build_dir'  : ('setup.py', 'build'),
        'builder'    : ('setup.py', 'gettext'),
        }
except ImportError:
    pass

# set options for uploading documentation to PyPI
if using_setuptools:
    command_options['upload_docs'] = {
        'upload_dir' : ('setup.py', 'doc/html'),
        }

# set options for building distributions
command_options['sdist'] = {
    'formats'        : ('setup.py', 'gztar zip'),
    'force_manifest' : ('setup.py', '1'),
    }

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

if using_setuptools:
    setup_kw['include_package_data'] = True

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
          'pywws' : ['services/*', 'lang/*/LC_MESSAGES/pywws.mo'],
          },
      scripts = scripts,
      data_files = data_files,
      cmdclass = cmdclass,
      command_options = command_options,
      **setup_kw
      )
