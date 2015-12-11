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
    def get(self, hostname, port='443', field=None):
        port = int(port) if port else 443

        x509 = yield self._blocking_download_certificate(hostname, port)
        response_data = format_response(hostname, port, x509)

        if field is not None:
            self._render_field(field, response_data['cert'],
                               response_data['request']['hostname'])
        else:
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

    def _render_field(self, field_name, cert, hostname):
        special_renderers = {
            'certificate.txt': (
                self._render_as_download, cert['certificate.txt'],
                'text/plain', 'certificate_{}.txt'.format(hostname)),

            'certificate.pem': (
                self._render_as_download, cert['certificate.pem'],
                'text/plain', 'certificate_{}.pem'.format(hostname)),

            'certificate.der': (
                self._render_as_download, cert['certificate.der'],
                'application/octet-stream',
                'certificate_{}.der'.format(hostname))
        }

        field_name = field_name.replace('-', '_')

        if field_name in special_renderers:
            logging.info(
                'Using special renderer for `{}`'.format(field_name))
            renderer_and_args = special_renderers[field_name]

        elif cert.get(field_name) is not None:  # Default: just send text
            logging.info(
                'Rendering `{}` with default (text)'.format(field_name))
            renderer_and_args = (self._render_as_text, cert[field_name])

        else:
            self.set_status(404)
            self.set_header('content-type', 'application/json')
            self.write('{"error": "No such field."}')
            return

        renderer_and_args[0](*renderer_and_args[1:])

    def _render_as_text(self, string):
        self.set_header('Content-Type', 'text/plain')
        self.write(string)

    def _render_as_download(self, obj, content_type, filename):
        self.set_header('Content-Type', content_type)
        self.set_header(
            'Content-Disposition',
            'attachment;filename="{}"'.format(filename))
        self.write(obj)

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

HOSTNAME_CAPTURE = r'(?P<hostname>' + HOSTNAME_REGEX + ')'
PORT_CAPTURE = r'(?P<port>\d{1,5})'
FIELD_CAPTURE = r'(?P<field>[a-z-.]+)'


def make_app(**kwargs):
    return tornado.web.Application(
        [
            (r"/" + HOSTNAME_CAPTURE + "/?",
             CertExpiryHandler),

            (r"/" + HOSTNAME_CAPTURE + ":" + PORT_CAPTURE + "/?",
             CertExpiryHandler),

            (r"/" + HOSTNAME_CAPTURE + '/' + FIELD_CAPTURE + "/?",
             CertExpiryHandler),

            (r"/" + HOSTNAME_CAPTURE + ":" + PORT_CAPTURE + '/'
             + FIELD_CAPTURE + "/?",
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
