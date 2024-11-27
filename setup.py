# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-24  pywws contributors

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

from __future__ import with_statement

from datetime import date
import os
from setuptools import setup
from setuptools import __version__ as setuptools_version
import sys

# read current version info without importing pywws package
if sys.version_info[0] >= 3:
    with open('src/pywws/__init__.py') as f:
        exec(f.read())
else:
    execfile('src/pywws/__init__.py')

# get GitHub repo information
# requires GitPython - 'pip install --user gitpython'
try:
    import git
except ImportError:
    git = None
if git:
    try:
        repo = git.Repo()
        if repo.is_dirty():
            latest = 0
            last_release = None
            for tag in repo.tags:
                if tag.tag.tagged_date > latest:
                    latest = tag.tag.tagged_date
                    last_release = str(tag)
            last_commit = str(repo.head.commit)[:7]
            # regenerate version info, if required
            if last_commit != _commit:
                _release = str(int(_release) + 1)
                _commit = last_commit
            if last_release:
                major, minor, patch = map(int, last_release.split('.'))
                today = date.today()
                year = today.year % 100
                if year == major and today.month == minor:
                    patch += 1
                else:
                    patch = 0
                __version__ = '{:d}.{:d}.{:d}'.format(year, today.month, patch)
            with open('src/pywws/__init__.py', 'r') as vf:
                old_init_str = vf.read()
            new_init_str = "__version__ = '" + __version__ + "'\n"
            new_init_str += "_release = '" + _release + "'\n"
            new_init_str += "_commit = '" + _commit + "'\n"
            if new_init_str != old_init_str:
                with open('src/pywws/__init__.py', 'w') as vf:
                    vf.write(new_init_str)
    except (git.exc.InvalidGitRepositoryError, git.exc.GitCommandNotFound):
        pass

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
    'directory' : ('setup.py', 'src/pywws/lang'),
    'use_fuzzy' : ('setup.py', '1'),
    }
command_options['extract_messages'] = {
    'input_dirs'         : ('setup.py', 'src/pywws'),
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
    'output_dir' : ('setup.py', 'src/pywws/lang'),
    'no_wrap'    : ('setup.py', '1'),
    }
command_options['update_catalog'] = {
    'domain'     : ('setup.py', 'pywws'),
    'input_file' : ('setup.py', 'build/gettext/pywws.pot'),
    'output_dir' : ('setup.py', 'src/pywws/lang'),
    'no_wrap'    : ('setup.py', '1'),
    }

# if sphinx is installed, add commands to build documentation
try:
    from sphinx.setup_command import BuildDoc
    # compile documentation to html
    cmdclass['build_sphinx'] = BuildDoc
    command_options['build_sphinx'] = {
        'source_dir' : ('setup.py', 'src/doc'),
        'build_dir'  : ('setup.py', 'doc'),
        'builder'    : ('setup.py', 'html'),
        }
    # extract strings for translation
    class extract_messages_doc(BuildDoc):
        description = 'extract localizable strings from the documentation'
    cmdclass['extract_messages_doc'] = extract_messages_doc
    command_options['extract_messages_doc'] = {
        'source_dir' : ('setup.py', 'src/doc'),
        'build_dir'  : ('setup.py', 'build'),
        'builder'    : ('setup.py', 'gettext'),
        }
except ImportError:
    pass

# set options for uploading documentation to PyPI
command_options['upload_docs'] = {
    'upload_dir' : ('setup.py', 'doc'),
    }

# set options for building distributions
command_options['sdist'] = {
    'formats'        : ('setup.py', 'gztar'),
    }


setup_kwds = {
    'cmdclass': cmdclass,
    'command_options': command_options,
    }


if tuple(map(int, setuptools_version.split('.')[:2])) < (61, 0):
    from setuptools import find_packages
    # get metadata from pyproject.toml
    import toml
    metadata = toml.load('pyproject.toml')
    with open(metadata['project']['readme']) as ldf:
        long_description = ldf.read()
    find_args = metadata['tool']['setuptools']['packages']['find']
    find_args['where'] = find_args['where'][0]
    packages = find_packages(**find_args)
    # add to setup arguments
    setup_kwds.update(
        version = __version__,
        name = metadata['project']['name'],
        author = metadata['project']['authors'][0]['name'],
        author_email = metadata['project']['authors'][0]['email'],
        url = metadata['project']['urls']['Homepage'],
        description = metadata['project']['description'],
        long_description = long_description,
        classifiers = metadata['project']['classifiers'],
        license = metadata['project']['license']['text'],
        packages = packages,
        package_dir = {'' : 'src'},
        package_data = metadata['tool']['setuptools']['package-data'],
        entry_points = {
            'console_scripts' : [
                '{} = {}'.format(k, v)
                for k, v in metadata['project']['scripts'].items()],
            },
        install_requires = metadata['project']['dependencies'],
        extras_require = metadata['project']['optional-dependencies'],
        zip_safe = metadata['tool']['setuptools']['zip-safe'],
        )

setup(**setup_kwds)
