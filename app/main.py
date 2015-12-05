#!/usr/bin/env python

import json
import logging
import time

from collections import OrderedDict

import tornado.ioloop
import tornado.web

from concurrent.futures import ThreadPoolExecutor
from tornado import gen
from tornado.concurrent import run_on_executor

from get_certificate import get_certificate_expiry

HOSTNAME_REGEX = '[a-zA-Z0-9.\-_]+'  # ish...


def get_certificate_info(hostname, port):
    return OrderedDict([
        ('request', OrderedDict([
            ('hostname', hostname),
            ('port', port),
        ])),
        ('certificate_expiry',
         str(get_certificate_expiry(hostname, port))),
    ])


class CertExpiryHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers=2)

    @gen.coroutine
    @tornado.web.removeslash
    def get(self, hostname, port='443'):
        port = int(port) if port else 443

        raw_data = yield self._blocking_get_cert_info(hostname, port)

        json_string = json.dumps(raw_data, indent=4)
        self.write(json_string)

    @run_on_executor
    def _blocking_get_cert_info(self, hostname, port):
        return get_certificate_info(hostname, port)


class TestSleepHandler(tornado.web.RequestHandler):
    # See https://gist.github.com/methane/2185380

    executor = ThreadPoolExecutor(max_workers=2)

    @gen.coroutine
    @tornado.web.removeslash
    def get(self, seconds):
        seconds = int(seconds)
        result = yield self._blocking_sleep(seconds)
        self.write(result)

    @run_on_executor
    def _blocking_sleep(self, seconds):
        time.sleep(seconds)
        return 'Slept {} seconds'.format(seconds)


def make_app(**kwargs):
    return tornado.web.Application(
        [
            (r"/(?P<hostname>" + HOSTNAME_REGEX + "):(?P<port>\d{1,5})/?",
             CertExpiryHandler),

            (r"/(?P<hostname>" + HOSTNAME_REGEX + ")/?",
             CertExpiryHandler),

            (r"/_test/sleep/(?P<seconds>\d{1,3})/?", TestSleepHandler),
        ],
        **kwargs)


if __name__ == "__main__":
    import os
    if os.environ.get('SSLDUMP_ENVIRONMENT', 'production') == 'development':
        print('DEBUG mode.')
        logging.basicConfig(level=logging.DEBUG)
        debug = True
    else:
        logging.basicConfig(level=logging.INFO)
        debug = False

    app = make_app(debug=debug)
    app.listen(8001)
    tornado.ioloop.IOLoop.current().start()
