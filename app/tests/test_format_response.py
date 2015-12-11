import json

from nose.tools import assert_in, assert_equal

from format_response import format_response

from . import load_example_x509


TEST_X509 = load_example_x509()
RESULT = format_response('dummy.com', 44399, TEST_X509)


def test_has_request_section():
    assert_in('request', RESULT)
    assert_equal(
        {'hostname': 'dummy.com', 'port': 44399},
        RESULT['request'])


def test_has_cert_section():
    assert_in('cert', RESULT)
    assert_equal(
        set([
            'serial_number',
            'expiry_datetime',
        ]),
        set(RESULT['cert'].keys()))


def test_certificate_expiry_datetime():
    assert_equal('2018-11-28T12:00:00Z', RESULT['cert']['expiry_datetime'])


def test_has_json_version_section():
    assert_in('json_version', RESULT)
    assert_equal(
        set([
            'serial_number',
            'expiry_datetime',
        ]),
        set(json.loads(RESULT['json_version']).keys()))
