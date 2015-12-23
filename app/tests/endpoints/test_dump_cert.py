import json

import mock

from nose.tools import assert_equal, assert_in

from tornado.testing import AsyncHTTPTestCase
from contextlib import contextmanager

from .. import load_example_x509

import main


EXPECTED_JSON = {
    'certificate_expiry': '2015-10-03T16:18:00Z',
    'hostname': 'example.com',
    'port': 443,
}


def assert_valid_json(string):
    try:
        json.loads(string)
    except ValueError as e:
        assert False, 'Failed to load as JSON: ' + repr(e)


@contextmanager
def setup_fake_response():
    x509 = load_example_x509()

    with mock.patch('main.get_certificate') as mocked_get_cert:
        mocked_get_cert.return_value = x509
        yield


class TestDumpCert(AsyncHTTPTestCase):
    def get_app(self):
        return main.make_app()

    def test_get_expiry(self):
        with setup_fake_response():
            response = self.fetch('/example.com', follow_redirects=False)

        assert_equal(200, response.code)
        assert_valid_json(response.body.decode('utf-8'))

    def test_get_expiry_trailing_slash_redirects(self):
        response = self.fetch('/example.com/', follow_redirects=False)
        assert_equal(301, response.code)
        assert_equal('/example.com', response.headers['location'])

    def test_get_serial_number(self):
        with setup_fake_response():
            response = self.fetch('/example.com/serial-number')

        assert_equal(200, response.code)
        assert_equal('text/plain', response.headers['content-type'])
        assert_equal('0e:64:c5:fb:c2:36:ad:e1:4b:17:2a:eb:41:c7:8c:b0',
                     response.body.decode('utf-8'))

    def test_get_expiry_datetime(self):
        with setup_fake_response():
            response = self.fetch('/example.com/expiry-datetime')

        assert_equal(200, response.code)
        assert_equal('text/plain', response.headers['content-type'])
        assert_equal('2018-11-28T12:00:00Z',
                     response.body.decode('utf-8'))

    def test_get_certificate_text(self):
        with setup_fake_response():
            response = self.fetch('/example.com/certificate.txt')

        assert_equal(200, response.code)
        assert_equal('text/plain', response.headers['content-type'])
        assert_equal('attachment;filename="certificate_example.com.txt"',
                     response.headers['content-disposition'])
        assert_equal(4223, len(response.body))

    def test_get_certificate_txt(self):
        with setup_fake_response():
            response = self.fetch('/example.com/certificate.pem')

        assert_equal(200, response.code)
        assert_equal('text/plain', response.headers['content-type'])
        assert_equal('attachment;filename="certificate_example.com.pem"',
                     response.headers['content-disposition'])
        assert_equal(2122, len(response.body))

    def test_get_certificate_asn1(self):
        with setup_fake_response():
            response = self.fetch('/example.com/certificate.der')

        assert_equal(200, response.code)
        assert_equal('application/octet-stream',
                     response.headers['content-type'])
        assert_equal('attachment;filename="certificate_example.com.der"',
                     response.headers['content-disposition'])
        assert_equal(1526, len(response.body))


class TestDumpCertContentTypeNegotiation(AsyncHTTPTestCase):
    def get_app(self):
        return main.make_app()

    def _get_response_for_header(self, accept_header):
        if accept_header is not None:
            headers = {'Accept': accept_header}
        else:
            headers = {}

        with setup_fake_response():
            return self.fetch(
                '/example.com',
                follow_redirects=False,
                headers=headers)

    def test_no_accept_header_returns_json(self):
        response = self._get_response_for_header(None)

        assert_equal(200, response.code)
        assert_equal('application/json', response.headers['content-type'])
        assert_valid_json(response.body.decode('utf-8'))

    def test_json_accept_header_returns_json(self):
        response = self._get_response_for_header('application/json')

        assert_equal(200, response.code)
        assert_equal('application/json', response.headers['content-type'])
        assert_valid_json(response.body.decode('utf-8'))

    def test_html_accept_header_returns_html(self):
        response = self._get_response_for_header(
            '"text/html,application/xhtml+xml,application/xml;'
            'q=0.9,*/*;q=0.8"')

        assert_equal(200, response.code)
        assert_in(
            '<h1>SSL/TLS certificate for example.com</h1>',
            response.body.decode('utf-8'))
        assert_equal(
            'text/html; charset=UTF-8',
            response.headers['content-type'])


class TestDumpCertNormalisation(AsyncHTTPTestCase):
    def get_app(self):
        return main.make_app()

    def assert_redirects(self, location, redirect_to):
        with setup_fake_response():
            response = self.fetch(location, follow_redirects=False)

        assert_equal(301, response.code)
        assert_equal(redirect_to, response.headers['location'])

    def test_default_port_is_removed(self):
        self.assert_redirects('/example.com:443', '/example.com')

    def test_hostname_is_lowercased(self):
        self.assert_redirects('/Example.com', '/example.com')

    def test_default_port_is_removed_with_field(self):
        self.assert_redirects(
            '/example.com:443/serial-number', '/example.com/serial-number')

    def test_hostname_is_lowercased_with_field(self):
        self.assert_redirects(
            '/Example.com/serial-number', '/example.com/serial-number')
