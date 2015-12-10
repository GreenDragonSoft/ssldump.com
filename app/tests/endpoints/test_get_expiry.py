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


class TestGetExpiry(AsyncHTTPTestCase):
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


class TestGetExpiryContentTypeNegotiation(AsyncHTTPTestCase):
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

    def test_html_accept_header_returns_json(self):
        response = self._get_response_for_header(
            '"text/html,application/xhtml+xml,application/xml;'
            'q=0.9,*/*;q=0.8"')

        assert_equal(200, response.code)
        assert_in('<h1>example.com</h1>', response.body.decode('utf-8'))
        assert_equal(
            'text/html; charset=UTF-8',
            response.headers['content-type'])
