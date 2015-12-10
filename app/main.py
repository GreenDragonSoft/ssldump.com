#!/usr/bin/env python

import json
import logging
import time

from os.path import dirname, join as pjoin

import tornado.ioloop
import tornado.web

from concurrent.futures import ThreadPoolExecutor
from tornado import gen
from tornado.concurrent import run_on_executor

from get_certificate import get_certificate
from format_response import format_response

HOSTNAME_REGEX = '[a-zA-Z0-9.\-_]+'  # ish...


class RenderToTemplateMixin(object):
    LOADER = tornado.template.Loader(
        pjoin(dirname(__file__), 'templates'))

    def render_to_template(self, template_name, args_dict):
        return self.LOADER.load(template_name).generate(**args_dict)


class CertExpiryHandler(tornado.web.RequestHandler, RenderToTemplateMixin):
    executor = ThreadPoolExecutor(max_workers=2)

    @gen.coroutine
    @tornado.web.removeslash
    def get(self, hostname, port='443'):
        port = int(port) if port else 443

        x509 = yield self._blocking_download_certificate(hostname, port)
        response_data = format_response(hostname, port, x509)

        json_string = json.dumps(response_data, indent=4)

        if client_accepts_html(self.request.headers.get('Accept')):

            self.write(self.render_to_template(
                'dump.html',
                {
                    'hostname': hostname,
                    'json_string': json_string,
                }
            ))

        else:
            self.set_header('Content-Type', 'application/json')
            self.write(json_string)

    @run_on_executor
    def _blocking_download_certificate(self, hostname, port):
        return get_certificate(hostname, port)


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


def client_accepts_html(accept_header):
    logging.warning('Accept header: `{}`'.format(accept_header))
    return accept_header is not None and 'text/html' in accept_header.lower()


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
