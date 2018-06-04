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
import pywws.logger
import pywws.storage
import pywws.template


class UploadThread(threading.Thread):
    def __init__(self, parent, context):
        super(UploadThread, self).__init__()
        self.parent = parent
        self.context = context
        self.queue = deque()

    def run(self):
        self.parent.logger.debug('thread started ' + self.name)
        self.old_message = ''
        if self.context.live_logging:
            polling_interval = self.parent.interval.total_seconds() / 20
            polling_interval = min(max(polling_interval, 4.0), 40.0)
        else:
            polling_interval = 4.0
        while not self.context.shutdown.is_set():
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
            self.parent.logger.debug('stopping thread ' + self.name)
            self.queue.append(None)

    def upload_batch(self):
        if not self.queue:
            return True
        OK = True
        count = 0
        with self.parent.session() as session:
            while self.queue and not self.context.shutdown.is_set():
                if self.parent.catchup == 0:
                    # "live only" service, so ignore old records
                    drop = len(self.queue) - 1
                    if self.queue[-1] is None:
                        drop -= 1
                    if drop > 0:
                        for i in range(drop):
                            self.queue.popleft()
                        self.parent.logger.warning(
                            '{:d} record(s) dropped'.format(drop))
                # send upload without taking it off queue
                upload = self.queue[0]
                if upload is None:
                    OK = False
                    break
                timestamp, kwds = upload
                OK, message = self.parent.upload_data(session, **kwds)
                self.log(message)
                if not OK:
                    break
                count += 1
                if timestamp:
                    self.context.status.set(
                        'last update', self.parent.service_name, str(timestamp))
                # finally remove upload from queue
                self.queue.popleft()
        if self.parent.log_count:
            if count > 1:
                self.parent.logger.warning('{:d} records sent'.format(count))
            elif count:
                self.parent.logger.info('1 record sent')
        return OK

    def log(self, message):
        if message == self.old_message:
            self.parent.logger.debug(message)
        else:
            self.parent.logger.error(message)
            self.old_message = message


class BaseToService(object):
    log_count = True

    def __init__(self, context):
        self.context = context
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
        self.last_update = self.context.status.get_datetime(
            'last update', self.service_name)
        # create upload thread
        self.upload_thread = UploadThread(self, context)
        self.stop = self.upload_thread.stop

    def upload(self, catchup=True, live_data=None, test_mode=False):
        OK = True
        count = 0
        for data, live in self.next_data(catchup and not test_mode, live_data):
            if count >= 30 or len(self.upload_thread.queue) >= 60:
                break
            timestamp = data['idx']
            if test_mode:
                timestamp = None
            prepared_data = self.prepare_data(data)
            prepared_data.update(self.fixed_data)
            self.upload_thread.queue.append(
                (timestamp, {'prepared_data': prepared_data, 'live': live}))
            count += 1
        # start upload thread
        if self.upload_thread.queue and not self.upload_thread.is_alive():
            self.upload_thread.start()

    def prepare_data(self, data):
        data_str = self.templater.make_text(self.template_file, data)
        self.template_file.seek(0)
        return eval('{' + data_str + '}')

    def next_data(self, catchup, live_data):
        if not catchup:
            start = self.context.calib_data.before(datetime.max)
        elif self.last_update:
            start = self.last_update + self.interval
        else:
            start = datetime.utcnow() - max(
                timedelta(days=self.catchup), self.interval)
        if live_data:
            stop = live_data['idx'] - self.interval
        else:
            stop = None
        next_update = start or datetime.min
        for data in self.context.calib_data[start:stop]:
            if data['idx'] >= next_update and self.valid_data(data):
                yield data, False
                self.last_update = data['idx']
                next_update = self.last_update + self.interval
        if (live_data and live_data['idx'] >= next_update and
                self.valid_data(live_data)):
            yield live_data, True
            self.last_update = live_data['idx']

    def valid_data(self, data):
        return True


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
    parser.add_argument('-c', '--catchup', action='store_true',
                        help='upload all data since last upload')
    parser.add_argument('-v', '--verbose', action='count',
                        help='increase amount of reassuring messages')
    parser.add_argument('data_dir', help='root directory of the weather data')
    args = parser.parse_args(argv[1:])
    pywws.logger.setup_handler(args.verbose or 0)
    with pywws.storage.pywws_context(args.data_dir) as context:
        uploader = class_(context)
        if 'register' in args and args.register:
            uploader.register()
            context.flush()
            return 0
        uploader.upload(catchup=args.catchup, test_mode=not args.catchup)
        uploader.stop()
    return 0
