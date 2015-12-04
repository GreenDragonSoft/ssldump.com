import json

import mock

from nose.tools import assert_equal
from tornado.testing import AsyncHTTPTestCase
from utcdatetime import utcdatetime

import main


class TestGetExpiry(AsyncHTTPTestCase):
    def get_app(self):
        return main.make_app()

    def test_get_expiry(self):
        with mock.patch('main.get_certificate_expiry') as mocked_get_expiry:
            mocked_get_expiry.return_value = utcdatetime(2015, 10, 3, 16, 18)
            response = self.fetch('/example.com', follow_redirects=False)

        assert_equal(200, response.code)
        assert_equal(
            {
                'certificate_expiry': '2015-10-03T16:18:00Z',
                'hostname': 'example.com',
                'port': 443,
            },
            json.loads(response.body.decode('utf-8')))

    def test_get_expiry_trailing_slash_redirects(self):
        response = self.fetch('/example.com/', follow_redirects=False)
        assert_equal(301, response.code)
        assert_equal('/example.com', response.headers['location'])
