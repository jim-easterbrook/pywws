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

"""Base classes for "service" uploaders."""

from __future__ import absolute_import, print_function, unicode_literals

from collections import deque
from datetime import datetime, timedelta
import os
import sys
import threading

if sys.version_info[0] >= 3:
    from io import StringIO
else:
    from StringIO import StringIO

import pywws
from pywws.constants import SECOND
import pywws.logger
import pywws.storage
import pywws.template


class Queue(deque):
    def __init__(self, start, *arg, **kw):
        super(Queue, self).__init__(*arg, **kw)
        self._start = start

    def append(self, x):
        super(Queue, self).append(x)
        if x is None:
            return
        self.append = super(Queue, self).append
        self._start()

    def full(self):
        return len(self) >= 50


class ServiceBase(threading.Thread):
    config = {}
    interval = timedelta(seconds=40)

    def __init__(self, context, check_params=True):
        super(ServiceBase, self).__init__()
        self.context = context
        self.queue = Queue(self.start)
        # get user configuration
        self.params = {}
        check = []
        for key, (default, required, fixed_key) in self.config.items():
            self.params[key] = context.params.get(
                self.service_name, key, default)
            if required:
                check.append(key)
            if fixed_key and self.params[key]:
                self.fixed_data[fixed_key] = self.params[key]
        # check values
        if check_params:
            self.check_params(*check)

    def check_params(self, *keys):
        for key in keys:
            if not self.params[key]:
                raise RuntimeError('"{}" not set in weather.ini'.format(key))

    def run(self):
        self.logger.debug('thread started ' + self.name)
        self.old_message = ''
        if self.context.live_logging:
            polling_interval = self.interval.total_seconds() / 20
            polling_interval = min(max(polling_interval, 4.0), 40.0)
        else:
            polling_interval = 4.0
        while not self.context.shutdown.is_set():
            OK = True
            if self.queue:
                try:
                    OK = self.upload_batch()
                except Exception as ex:
                    self.log(str(ex))
                    OK = False
            if OK:
                pause = polling_interval
            elif self.context.live_logging:
                # upload failed, wait before trying again
                pause = 40.0
            else:
                # upload failed or nothing more to do
                break
            self.context.shutdown.wait(pause)

    def stop(self):
        if self.is_alive():
            self.logger.debug('stopping thread ' + self.name)
            self.queue.append(None)

    def log(self, message):
        if message == self.old_message:
            self.logger.debug(message)
        else:
            self.logger.error(message)
            self.old_message = message


class DataServiceBase(ServiceBase):
    catchup = 7
    fixed_data = {}

    def __init__(self, context, check_params=True):
        super(DataServiceBase, self).__init__(context, check_params)
        # check config
        template = context.params.get(self.service_name, 'template')
        if template == 'default':
            context.params.unset(self.service_name, 'template')
        elif template:
            self.logger.critical(
                'obsolete item "template" found in weather.ini '
                'section [{}]'.format(self.service_name))
        # create templater
        if self.template:
            self.templater = pywws.template.Template(context, use_locale=False)
            self.template_file = StringIO(self.template)
        # get time stamp of last uploaded data
        self.last_update = context.status.get_datetime(
            'last update', self.service_name)
        if not self.last_update:
            self.last_update = datetime.utcnow() - timedelta(days=self.catchup)

    def queue_data(self, timestamp, data, live):
        if timestamp and timestamp < self.last_update + self.interval:
            return False
        if not self.valid_data(data):
            return False
        data_str = self.templater.make_text(self.template_file, data)
        self.template_file.seek(0)
        prepared_data = eval('{' + data_str + '}')
        prepared_data.update(self.fixed_data)
        self.logger.debug('data: %s', str(prepared_data))
        self.queue.append((timestamp, prepared_data, live))
        if timestamp:
            self.last_update = timestamp
        return True

    def valid_data(self, data):
        return True

    def upload_batch(self):
        OK = True
        count = 0
        with self.session() as session:
            while self.queue and not self.context.shutdown.is_set():
                # send upload without taking it off queue
                upload = self.queue[0]
                if upload is None:
                    OK = False
                    break
                timestamp, prepared_data, live = upload
                OK, message = self.upload_data(
                    session, prepared_data=prepared_data, live=live)
                self.log(message)
                if not OK:
                    break
                count += 1
                if timestamp:
                    self.context.status.set(
                        'last update', self.service_name, str(timestamp))
                # finally remove upload from queue
                self.queue.popleft()
        if count > 1:
            self.logger.warning('{:d} records sent'.format(count))
        elif count:
            self.logger.info('1 record sent')
        return OK


class CatchupDataService(DataServiceBase):
    def do_catchup(self, do_all=False):
        start = self.last_update + self.interval
        if do_all:
            for data in self.context.calib_data[start:]:
                while self.queue.full():
                    self.context.shutdown.wait(4.0)
                    if self.context.shutdown.is_set():
                        return True
                self.queue_data(data['idx'], data, False)
            return True
        for data in self.context.calib_data[start:]:
            if self.queue.full():
                return True
            if self.queue_data(data['idx'], data, False):
                return False
        return True

    def upload(self, live_data=None, test_mode=False, option=''):
        if self.queue.full():
            return
        if test_mode:
            idx = self.context.calib_data.before(datetime.max)
        else:
            idx = self.context.calib_data.after(self.last_update + self.interval)
        while idx:
            data = self.context.calib_data[idx]
            timestamp = data['idx']
            idx = self.context.calib_data.after(timestamp + SECOND)
            if test_mode:
                timestamp = None
            if self.queue_data(timestamp, data, False):
                break
        if live_data and not idx:
            self.queue_data(live_data['idx'], live_data, True)


class LiveDataService(DataServiceBase):
    def do_catchup(self, do_all=False):
        return True

    def upload(self, live_data=None, test_mode=False, option=''):
        if self.queue.full():
            return
        if live_data:
            data = live_data
        else:
            idx = self.context.calib_data.before(datetime.max)
            if not idx:
                return
            data = self.context.calib_data[idx]
        timestamp = data['idx']
        if test_mode:
            timestamp = None
        self.queue_data(timestamp, data, bool(live_data))

    def upload_batch(self):
        # remove stale uploads from queue
        drop = len(self.queue) - 1
        if self.queue[-1] is None:
            drop -= 1
        if drop > 0:
            for i in range(drop):
                self.queue.popleft()
            self.logger.warning('{:d} record(s) dropped'.format(drop))
        # send most recent data
        return super(LiveDataService, self).upload_batch()


class FileService(ServiceBase):
    def do_catchup(self, do_all=False):
        for upload in eval(
                self.context.status.get('pending', self.service_name, '[]')):
            self.upload(option=upload)
        return True

    def upload(self, live_data=None, option=''):
        if self.queue.full() or (option in self.queue):
            return
        self.queue.append(option)

    def upload_batch(self):
        pending = eval(
            self.context.status.get('pending', self.service_name, '[]'))
        OK = True
        with self.session() as session:
            while self.queue and not self.context.shutdown.is_set():
                upload = self.queue[0]
                if upload is None:
                    OK = False
                    break
                if os.path.isabs(upload):
                    path = upload
                else:
                    path = os.path.join(self.context.output_dir, upload)
                self.logger.debug('file: %s', path)
                OK, message = self.upload_file(session, path)
                self.log(message)
                if OK:
                    if upload in pending:
                        pending.remove(upload)
                else:
                    if upload not in pending:
                        pending.append(upload)
                    break
                self.queue.popleft()
        self.context.status.set('pending', self.service_name, repr(pending))
        return OK


def main(class_, argv=None):
    import argparse
    import inspect

    if argv is None:
        argv = sys.argv
    docstring = inspect.getdoc(sys.modules[class_.__module__]).split('\n\n')
    parser = argparse.ArgumentParser(
        description=docstring[0], epilog=docstring[1])
    if hasattr(class_, 'register'):
        parser.add_argument('-r', '--register', action='store_true',
                            help='register (or update) with service')
    if issubclass(class_, CatchupDataService):
        parser.add_argument('-c', '--catchup', action='store_true',
                            help='upload all data since last upload')
    parser.add_argument('-v', '--verbose', action='count',
                        help='increase amount of reassuring messages')
    parser.add_argument('data_dir', help='root directory of the weather data')
    if issubclass(class_, FileService):
        parser.add_argument('file', nargs='*', help='file to be uploaded')
    args = parser.parse_args(argv[1:])
    pywws.logger.setup_handler(args.verbose or 0)
    with pywws.storage.pywws_context(args.data_dir) as context:
        if 'register' in args and args.register:
            uploader = class_(context, check_params=False)
            uploader.register()
            context.flush()
            return 0
        uploader = class_(context)
        if issubclass(class_, FileService):
            for file in args.file:
                uploader.upload(option=os.path.abspath(file))
        elif issubclass(class_, CatchupDataService) and args.catchup:
            uploader.do_catchup(do_all=True)
        else:
            uploader.upload(test_mode=True)
        uploader.stop()
    return 0
