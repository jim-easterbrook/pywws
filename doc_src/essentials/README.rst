README
======

Python software for USB Wireless WeatherStations (pywws).
  http://code.google.com/p/pywws/

Copyright 2008-12 Jim Easterbrook (jim@jim-easterbrook.me.uk), derived from previous work by Michael Pendec (michael.pendec@gmail.com) and Svend Skafte (svend@skafte.net)

This software is not released through any official channels, and therefore do not expect any support.

This software is in no way affiliated or related to
  http://www.foshk.com, Fine Offset Electronics Co.,LTD.

Licence terms:
  This softare is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

  This softare is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with this softare; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Dependencies:

* Python (http://www.python.org/) version 2.4 or higher
  (note: Python 3 is not yet supported)
* USB library:

  * option 1 (best for small systems such as routers):

     * libusb (http://www.libusb.org/) version 0.1.12
       (note: libusb 1 is not supported)
     * PyUSB (http://sourceforge.net/apps/trac/pyusb/) version 0.4.x
  * option 2 (best for Linux PCs and Macs):

     * hidapi (https://github.com/signal11/hidapi)
       (note: hidapi on Linux can use libusb version 1.0)
     * cython-hidapi (https://github.com/gbishop/cython-hidapi)
     * cython (http://cython.org/)
* For graph drawing:

  * gnuplot (http://www.gnuplot.info/) v4.2 or higher
* For secure website uploading (sftp):

  * paramiko (http://www.lag.net/paramiko/)
  * pycrypto (http://www.dlitz.net/software/pycrypto/)
* For Twitter updates:

  * tweepy (http://code.google.com/p/tweepy/)
  * simplejson (http://pypi.python.org/pypi/simplejson)
    (note: simplejson is included in Python 2.6 or higher)
* To create new language translations:

  * gettext (http://www.gnu.org/s/gettext/)

Many of these dependencies are available as packages for most Linux distributions. This provides an easier way to install them than downloading source from the project websites. Note that the package names may be slightly different, e.g. python-usb instead of pyusb.

This software collection currently includes the following files:

* README.txt                      -- you are reading it!
* CHANGELOG.txt                   -- development history
* LICENCE.txt                     -- GNU General Public License
* setup.py                        -- build & install pywws
* makefile                        -- compiles language files and documentation
* doc/html/\*                     -- HTML documentation of most of the above
* doc/text/\*                     -- plain text documentation
* doc_src/\*                      -- documentation source files
* code/\*.py                      -- pywws Python scripts
* code/pywws/\*.py                -- the pywws software modules
* code/example_graph_templates/\* -- example graph XML "recipes"
* code/example_templates/\*       -- example text templates
* code/example_modules/\*         -- example calibration modules
* code/languages/\*               -- language source files

Upgrading from earlier versions:
  Back up your data, then run Reprocess.py to regenerate summary data.

Getting started:
  See doc/guides/getstarted: :doc:`../guides/getstarted`.

Comments or questions? Please subscribe to the pywws mailing list http://groups.google.com/group/pywws and let us know.
