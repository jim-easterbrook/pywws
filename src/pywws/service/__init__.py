# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2018  pywws contributors

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

from __future__ import absolute_import, print_function, unicode_literals

import argparse
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timedelta
import logging
import os
import sys
import threading
import time

if sys.version_info[0] >= 3:
    from io import StringIO
else:
    from StringIO import StringIO

import requests

import pywws
import pywws.logger
import pywws.storage
import pywws.template


class BaseUploader(threading.Thread):
    def __init__(self, context, fixed_data):
        super(BaseUploader, self).__init__()
        self.context = context
        self.queue = deque()
        self.fixed_data.update(fixed_data)

    def run(self):
        old_response = ''
        pause = 0
        count = 0
        with self.session() as session:
            while not self.context.shutdown.is_set():
                if pause:
                    pause -= 1
                elif self.queue:
                    # look at upload without taking it off queue
                    upload = self.queue[0]
                    if not upload:
                        return
                    timestamp, prepared_data, live = upload
                    prepared_data.update(self.fixed_data)
                    response = self.upload(session, prepared_data, live)
                    if response:
                        if response == old_response:
                            self.logger.debug(response)
                        else:
                            self.logger.error(response)
                            old_response = response
                        # upload failed, wait before trying again
                        pause = 60
                    else:
                        count += 1
                        if timestamp:
                            self.context.status.set(
                                'last update', self.service_name, str(timestamp))
                        # finally remove upload from queue
                        self.queue.popleft()
                    if count and (pause or not self.queue):
                        if count > 1:
                            self.logger.info('{:d} records sent'.format(count))
                        else:
                            self.logger.debug('1 record sent')
                        count = 0
                time.sleep(1)


class BaseToService(object):
    def __init__(self, context, uploader):
        self.context = context
        # create templater
        self.templater = pywws.template.Template(context, use_locale=False)
        self.template_file = StringIO(self.template)
        # set timestamp of first data to upload
        earliest = datetime.utcnow() - max(
            timedelta(days=self.catchup), self.interval)
        self.next_update = context.status.get_datetime(
            'last update', self.service_name)
        if self.next_update:
            self.next_update += self.interval
            self.next_update = max(self.next_update, earliest)
        else:
            self.next_update = earliest
        # start upload thread
        self.upload_thread = uploader
        self.upload_thread.start()

    def upload(self, catchup=True, live_data=None, test_mode=False):
        OK = True
        count = 0
        if test_mode:
            self.next_update = min(
                self.next_update, self.context.calib_data.before(datetime.max))
        for data, live in self.next_data(catchup, live_data):
            if max(count, len(self.upload_thread.queue)) >= 20:
                break
            timestamp = data['idx']
            if test_mode:
                timestamp = None
            # convert data
            data_str = self.templater.make_text(self.template_file, data)
            self.template_file.seek(0)
            prepared_data = eval('{' + data_str + '}')
            if len(prepared_data) < 2:
                # need at least idx plus one other item of data
                continue
            self.upload_thread.queue.append((timestamp, prepared_data, live))
            count += 1

    def next_data(self, catchup, live_data):
        if catchup:
            start = self.next_update
        else:
            start = self.context.calib_data.before(datetime.max)
        if live_data:
            stop = live_data['idx'] - self.interval
        else:
            stop = None
        for data in self.context.calib_data[start:stop]:
            if data['idx'] >= self.next_update:
                yield data, False
                self.next_update = data['idx'] + self.interval
        if live_data and live_data['idx'] >= self.next_update:
            yield live_data, True
            self.next_update = live_data['idx'] + self.interval

    def shutdown(self):
        self.logger.debug('stopping upload thread')
        # tell upload queue to terminate cleanly
        self.upload_thread.queue.append(None)
        # wait for thread to finish
        self.upload_thread.join()


def main(ToService, description, argv=None):
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--catchup', action='store_true',
                        help='upload all data since last upload')
    parser.add_argument('-v', '--verbose', action='count',
                        help='increase amount of reassuring messages')
    parser.add_argument('data_dir', help='root directory of the weather data')
    args = parser.parse_args(argv)
    pywws.logger.setup_handler(args.verbose)
    with pywws.storage.pywws_context(args.data_dir) as context:
        uploader = ToService(context)
        uploader.upload(catchup=args.catchup, test_mode=not args.catchup)
        uploader.shutdown()
    return 0
