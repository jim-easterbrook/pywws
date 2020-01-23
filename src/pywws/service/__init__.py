# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2018-20  pywws contributors

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

"""Base classes for "service" uploaders.

.. inheritance-diagram:: CatchupDataService FileService LiveDataService
    :top-classes: pywws.service.ServiceBase

"""

from __future__ import absolute_import, print_function, unicode_literals

from ast import literal_eval
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
        """Are there already too many uploads on the queue."""
        return len(self) >= 50


class ServiceBase(threading.Thread):
    """Base class for all service uploaders.

    Uploaders use a separate thread to allow the main program thread to
    continue even if a service is slow to respond. Items to upload are
    passed to the thread via a thread safe queue. The thread is started
    when the first item is put on the queue. To shut down the thread put
    :py:obj:`None` on the queue, e.g. by calling :py:meth:`stop`.

    There are two types of uploader derived from this class.
    :py:class:`DataServiceBase` is used by uploaders that send defined
    sets of data, typically as an HTML "post" or "get" operation.
    :py:class:`FileService` is used to upload files, including free form
    text such as a Twitter message.

    All service classes must provide a :py:attr:`logger` object so that
    logging messages carry the right module name, and define a
    :py:attr:`service_name` string. They must also define a
    :py:meth:`session` method.
    """

    config = {}
    """Defines the user configuration of the uploader. Each item must be
    of the form ``name: (default (str), required (bool), fixed_key (str
    or None))``. ``name`` is the ``weather.ini`` value name, ``default``
    is a default value, ``required`` defines whether a value must be
    supplied at run time, and ``fixed_key`` defines if and to where in
    :py:attr:`~DataServiceBase.fixed_data` the value should be copied.
    """

    interval = timedelta(seconds=40)
    """Sets the minimum period between the timestamps of uploaded data.
    For some services this can be less than the weather station's "live"
    data period (48 seconds) whereas others may require 5 or 15 minutes
    between readings.
    """

    logger = None
    """A :py:class:`logging.Logger` object created with the module name.
    This is typically done as follows::

        logger = logging.getLogger(__name__)
    """

    service_name = ''
    """A short name used to refer to the service in weather.ini. It
    should be all lower case. The best name to use is the last part of
    the module's file name, as follows::

        service_name = os.path.splitext(os.path.basename(__file__))[0]
    """

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
                # copy fixed_data to avoid changing class definition
                self.fixed_data = dict(self.fixed_data)
                self.fixed_data[fixed_key] = self.params[key]
        # check values
        if check_params:
            self.check_params(*check)

    def check_params(self, *keys):
        """Ensure user has set required values in weather.ini.

        Normally the :py:data:`~ServiceBase.config` names with
        ``required`` set are checked, but if your uploader has a
        ``register`` method you may need to check for other data.

        :param str keys: the :py:data:`~ServiceBase.config` names to
            verify.
        """

        for key in keys:
            if not self.params[key]:
                raise RuntimeError('"{}" not set in weather.ini'.format(key))

    def session(self):
        """Context manager factory function for a batch of one or more
        uploads.

        This makes it easy to ensure any resources such as an internet
        connection are properly closed after a batch of uploads. Use the
        :py:func:`contextlib.contextmanager` decorator when you
        implement this method.

        For a typical example, see the source code of the
        :py:mod:`pywws.service.openweathermap` module. If your upload
        can't benefit from a session object yield :py:obj:`None`, as in
        :py:mod:`pywws.service.copy`.
        """
        raise NotImplementedError()

    def run(self):
        """ """
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
                    self.logger.exception(ex)
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
    """Base class for "data" services.

    A "data" service uploader sends defined sets of data, typically as
    an HTML "post" or "get" operation. Service classes should be based
    on :py:class:`CatchupDataService` or :py:class:`LiveDataService`,
    depending on whether the service allows uploading of past data, for
    example to fill in gaps if the server (or pywws client) goes down
    for a few hours or days.

    Data service classes must provide a :py:attr:`template` string to
    define how to convert pywws data before uploading. Required methods
    are :py:meth:`~ServiceBase.session` and :py:meth:`upload_data`. If
    the service has a separate authorisation or registration process
    this can be done in a :py:meth:`~pywws.service.mastodon.register`
    method. See :py:mod:`pywws.service.mastodon` for an example.
    """

    template = ''
    """Defines the conversion of pywws data to key, value pairs required
    by the service. The template string is passed to
    :py:mod:`pywws.template`, then the result is passed to
    :py:func:`~ast.literal_eval` to create a :py:obj:`dict`. This rather
    complex process allows great flexibility, but you do have to be
    careful with use of quotation marks. """

    fixed_data = {}
    """Defines a set of ``key: value`` pairs that are the same for every
    data upload. This might include the station's location or the
    software name & version. Values set by the user should be included
    in the weather.ini config defined in :py:data:`~ServiceBase.config`.
    """

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
            self.template_file = None
        # get time stamp of last uploaded data
        self.last_update = context.status.get_datetime(
            'last update', self.service_name)
        if not self.last_update:
            if self.catchup:
                self.last_update = datetime.utcnow() - timedelta(
                    days=self.catchup)
            else:
                self.last_update = datetime.min

    def upload_data(self, session, prepared_data={}):
        """Upload one data set to the service.

        Every data service class must implement this method.

        :param object session: the object created by
            :py:meth:`~ServiceBase.session`. This is typically used to
            communicate with the server and is automatically closed when
            a batch of uploads has finished.
        :param dict prepared_data: a set of key: value pairs to upload.
            The keys and values must all be text strings.
        """
        raise NotImplementedError()

    def queue_data(self, timestamp, data):
        if not self.valid_data(data):
            return False
        prepared_data = self.prepare_data(data)
        prepared_data.update(self.fixed_data)
        self.logger.debug('data: %s', str(prepared_data))
        self.queue.append((timestamp, prepared_data))
        return True

    def prepare_data(self, data):
        if not self.template_file:
            self.template_file = StringIO(self.template)
        data_str = self.templater.make_text(self.template_file, data)
        self.template_file.seek(0)
        return literal_eval('{' + data_str + '}')

    def valid_data(self, data):
        return True


class CatchupDataService(DataServiceBase):
    catchup = 7
    """Sets the number of days of past data that can be uploaded when a
    service is first used.
    """

    def queue_data(self, timestamp, data):
        if timestamp and timestamp < self.last_update + self.interval:
            return False
        OK = super(CatchupDataService, self).queue_data(timestamp, data)
        if OK and timestamp:
            self.last_update = timestamp
        return OK

    def do_catchup(self, do_all=False):
        start = self.last_update + self.interval
        if do_all:
            for data in self.context.calib_data[start:]:
                while self.queue.full():
                    self.context.shutdown.wait(4.0)
                    if self.context.shutdown.is_set():
                        return True
                self.queue_data(data['idx'], data)
            return True
        for data in self.context.calib_data[start:]:
            if self.queue.full():
                return True
            if self.queue_data(data['idx'], data):
                return False
        return True

    def upload(self, live_data=None, test_mode=False, options=()):
        if self.queue.full():
            return
        if test_mode:
            start = self.context.calib_data.before(datetime.max)
        else:
            start = self.last_update + self.interval
        for data in self.context.calib_data[start:]:
            timestamp = data['idx']
            if test_mode:
                timestamp = None
            if self.queue_data(timestamp, data):
                return
        if live_data:
            self.queue_data(live_data['idx'], live_data)

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
                timestamp, prepared_data = upload
                OK, message = self.upload_data(
                    session, prepared_data=prepared_data)
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


class LiveDataService(DataServiceBase):
    catchup = None

    def do_catchup(self, do_all=False):
        return True

    def upload(self, live_data=None, test_mode=False, options=()):
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
        self.queue_data(timestamp, data)

    def upload_batch(self):
        # get most recent upload on queue
        upload = self.queue.popleft()
        while self.queue and self.queue[0] is not None:
            upload = self.queue.popleft()
        if upload is None:
            return False
        timestamp, prepared_data = upload
        # check time since last upload
        if timestamp and timestamp < self.last_update + self.interval:
            return True
        with self.session() as session:
            OK, message = self.upload_data(session, prepared_data=prepared_data)
        self.log(message)
        if OK:
            self.logger.info('1 record sent')
            if timestamp:
                self.last_update = timestamp
                self.context.status.set(
                    'last update', self.service_name, str(timestamp))
        return OK


class FileService(ServiceBase):
    """Base class for "file" services.

    """
    def do_catchup(self, do_all=False):
        self.upload(options=literal_eval(
            self.context.status.get('pending', self.service_name, '[]')))
        return True

    def upload(self, live_data=None, options=()):
        for item in options:
            if self.queue.full() or (item in self.queue):
                continue
            self.queue.append(item)

    def upload_batch(self):
        pending = literal_eval(
            self.context.status.get('pending', self.service_name, '[]'))
        OK = True
        count = 0
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
                if not os.path.isfile(path):
                    if upload in pending:
                        pending.remove(upload)
                    self.queue.popleft()
                    continue
                self.logger.debug('file: %s', path)
                OK, message = self.upload_file(session, path)
                self.log(message)
                if OK:
                    if upload in pending:
                        pending.remove(upload)
                    count += 1
                else:
                    if upload not in pending:
                        pending.append(upload)
                    break
                self.queue.popleft()
        self.context.status.set('pending', self.service_name, repr(pending))
        if count > 1:
            self.logger.info('{:d} uploads'.format(count))
        elif count:
            self.logger.info('1 upload')
        return OK


def main(class_, argv=None):
    import argparse
    import inspect

    if argv is None:
        argv = sys.argv
    docstring = inspect.getdoc(sys.modules[class_.__module__])
    if sys.version_info[0] < 3:
        docstring = docstring.decode('utf-8')
    docstring = docstring.split('\n\n')
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
            uploader.upload(options=map(os.path.abspath, args.file))
        elif issubclass(class_, CatchupDataService) and args.catchup:
            uploader.do_catchup(do_all=True)
        else:
            uploader.upload(test_mode=True)
        uploader.stop()
    return 0
