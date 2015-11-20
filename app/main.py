#!/usr/bin/env python

import logging
import time

import tornado.ioloop
import tornado.web

from concurrent.futures import ThreadPoolExecutor
from tornado import gen
from tornado.concurrent import run_on_executor

from get_certificate import get_certificate_expiry

HOSTNAME_REGEX = '[a-zA-Z0-9.\-_]+'  # ish...


class CertExpiryHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers=2)

    @gen.coroutine
    @tornado.web.addslash
    def get(self, hostname, port='443'):
        port = int(port) if port else 443

        expiry_date = yield self._blocking_get_cert_expiry(hostname, port)
        self.write(str(expiry_date))

    @run_on_executor
    def _blocking_get_cert_expiry(self, hostname, port):
        return get_certificate_expiry(hostname, port)


class TestSleepHandler(tornado.web.RequestHandler):
    # See https://gist.github.com/methane/2185380

    executor = ThreadPoolExecutor(max_workers=2)

    @gen.coroutine
    @tornado.web.addslash
    def get(self, seconds):
        seconds = int(seconds)
        result = yield self._blocking_sleep(seconds)
        self.write(result)

    @run_on_executor
    def _blocking_sleep(self, seconds):
        time.sleep(seconds)
        return 'Slept {} seconds'.format(seconds)


def make_app():
    return tornado.web.Application([
        (r"/(?P<hostname>" + HOSTNAME_REGEX + "):(?P<port>\d{1,5})/?",
         CertExpiryHandler),

        (r"/(?P<hostname>" + HOSTNAME_REGEX + ")/?",
         CertExpiryHandler),

        (r"/_test/sleep/(?P<seconds>\d{1,3})/?", TestSleepHandler),
    ])

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = make_app()
    app.listen(8001)
    tornado.ioloop.IOLoop.current().start()
