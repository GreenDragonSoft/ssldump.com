import json
import unittest

import mock

from nose.tools import assert_equal, assert_in

from tornado.testing import AsyncHTTPTestCase
from contextlib import contextmanager

from utcdatetime import utcdatetime

import main


EXPECTED_JSON = {
    'certificate_expiry': '2015-10-03T16:18:00Z',
    'hostname': 'example.com',
    'port': 443,
}


@contextmanager
def setup_fake_response():
    with mock.patch('main.get_certificate_info') as mocked_get_cert:
        mocked_get_cert.return_value = EXPECTED_JSON
        yield


class TestGetExpiry(AsyncHTTPTestCase):
    def get_app(self):
        return main.make_app()

    def test_get_expiry(self):
        with setup_fake_response():
            response = self.fetch('/example.com', follow_redirects=False)

        assert_equal(200, response.code)
        assert_equal(EXPECTED_JSON, json.loads(response.body.decode('utf-8')))

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
        assert_equal(EXPECTED_JSON, json.loads(response.body.decode('utf-8')))
        assert_equal('application/json', response.headers['content-type'])

    def test_json_accept_header_returns_json(self):
        response = self._get_response_for_header('application/json')

        assert_equal(200, response.code)
        assert_equal(EXPECTED_JSON, json.loads(response.body.decode('utf-8')))
        assert_equal('application/json', response.headers['content-type'])

    def test_html_accept_header_returns_json(self):
        response = self._get_response_for_header(
            '"text/html,application/xhtml+xml,application/xml;'
            'q=0.9,*/*;q=0.8"')

        assert_equal(200, response.code)
        assert_in('<h1>example.com</h1>', response.body.decode('utf-8'))
        assert_equal(
            'text/html; charset=UTF-8',
            response.headers['content-type'])


class TestGetCertificateInfo(unittest.TestCase):
    def test_result_structure(self):
        with mock.patch('main.get_certificate_expiry') as mocked_get_expiry:
            mocked_get_expiry.return_value = utcdatetime(2015, 6, 7, 13, 52)
            result = main.get_certificate_info('example.com', 443)

        result = json.loads(json.dumps(result))
        assert_equal(
            set(['request', 'certificate_expiry']),
            set(result.keys()))

        assert_equal(
            {'hostname': 'example.com', 'port': 443},
            result['request'])

        assert_equal('2015-06-07T13:52:00Z', result['certificate_expiry'])
