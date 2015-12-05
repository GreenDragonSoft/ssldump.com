import json
import unittest

import mock

from nose.tools import assert_equal
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
