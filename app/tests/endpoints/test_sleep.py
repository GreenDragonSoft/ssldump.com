import mock

from nose.tools import assert_equal
from tornado.testing import AsyncHTTPTestCase

import main


class TestSleep(AsyncHTTPTestCase):
    def get_app(self):
        return main.make_app()

    def test_http_sleep(self):
        with mock.patch('time.sleep') as mocked_sleep:
            response = self.fetch('/_test/sleep/2', follow_redirects=False)

        mocked_sleep.assert_called_once_with(2)

        assert_equal(200, response.code)
        assert_equal(b'Slept 2 seconds', response.body)

    def test_http_sleep_trailing_slash_redirects(self):
        response = self.fetch('/_test/sleep/2/', follow_redirects=False)
        assert_equal(301, response.code)
        assert_equal('/_test/sleep/2', response.headers['location'])
