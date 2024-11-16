# python-gphoto2 - Python interface to libgphoto2
# http://github.com/jim-easterbrook/python-gphoto2
# Copyright (C) 2024  pywws contributors
#
# This file is part of pywws.
#
# pywws is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# pywws is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with pywws.  If not, see
# <https://www.gnu.org/licenses/>.

import os
import sys

# requires GitPython - 'pip install --user gitpython'
import git


# get root dir
root = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
# read current version info without importing pywws package
init_file = os.path.join(root, 'src', 'pywws', '__init__.py')
if sys.version_info[0] >= 3:
    with open('src/pywws/__init__.py') as f:
        exec(f.read())
else:
    execfile('src/pywws/__init__.py')


def main(argv=None):
    # create git message
    message = __version__ + '\n\n'
    with open(os.path.join(root, 'CHANGELOG.txt')) as cl:
        while not cl.readline().startswith('Changes'):
            pass
        while True:
            line = cl.readline().strip()
            if not line:
                break
            message += line + '\n'
    repo = git.Repo()
    tag = repo.create_tag(__version__, message=message)
    remote = repo.remotes.origin
    remote.push(tags=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
