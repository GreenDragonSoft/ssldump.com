#!/usr/bin/env python

import logging
import time

from os.path import dirname, join as pjoin

import tornado.ioloop
import tornado.web

from concurrent.futures import ThreadPoolExecutor
from tornado import gen
from tornado.concurrent import run_on_executor

from jinja2 import Environment, FileSystemLoader

import OpenSSL

from get_certificate import get_certificate
from format_response import format_response

HOSTNAME_REGEX = '[a-zA-Z0-9.\-_]+'  # ish...


def load_example_x509():
    filename = pjoin(
        dirname(__file__), 'tests', 'sample_data', 'example.com.pem')
    with open(filename, 'rb') as f:
        return OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, f.read())


class RenderToTemplateMixin(object):
    ENV = Environment(loader=FileSystemLoader(
        [pjoin(dirname(__file__), 'templates')]))

    def render_to_template(self, template_name, args_dict):
        template = self.ENV.get_template(template_name)
        return template.render(args_dict)


class CertExpiryHandler(tornado.web.RequestHandler, RenderToTemplateMixin):
    executor = ThreadPoolExecutor(max_workers=2)

    @gen.coroutine
    @tornado.web.removeslash
    def get(self, hostname, port='443'):
        port = int(port) if port else 443

        x509 = yield self._blocking_download_certificate(hostname, port)
        response_data = format_response(hostname, port, x509)

        self._render(response_data)

    def _render(self, response_data):
        response_data['uri'] = '{}://{}{}'.format(
            self.request.protocol,
            self.request.host,
            self.request.uri)

        if client_accepts_html(self.request.headers.get('Accept')):

            self.write(self.render_to_template('dump.html', response_data))

        else:
            self.set_header('Content-Type', 'application/json')
            json_string = response_data['json_version']
            self.write(json_string)

    @run_on_executor
    def _blocking_download_certificate(self, hostname, port):
        return get_certificate(hostname, port)


class TestCertExpiryHandler(CertExpiryHandler):
    def get(self):

        x509 = load_example_x509()
        self._render(format_response('example.com', 443, x509))


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

            (r"/_test/example.com",
             TestCertExpiryHandler),

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
