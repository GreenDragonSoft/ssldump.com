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
            'certificate.der',
            'certificate.der.txt',
            'certificate.txt',
            'certificate.pem',
            'subject_state',
            'email_address',
            'subject_country',
            'subject_common_name',
            'subject_postal_code',
            'subject_locality',
            'subject_organization',
            'subject_organizational_unit',
            'subject_street',
            'sha1_fingerprint',
            'sha256_fingerprint',

        ]),
        set(RESULT['cert'].keys()))


def test_certificate_expiry_datetime():
    assert_equal('2018-11-28T12:00:00Z', RESULT['cert']['expiry_datetime'])


def test_sha1_fingerprint():
    assert_equal(
        '25:09:fb:22:f7:67:1a:ea:2d:0a:28:ae:80:51:6f:39:0d:e0:ca:21',
        RESULT['cert']['sha1_fingerprint'])


def test_sha256_fingerprint():
    assert_equal(
        ('64:2d:e5:4d:84:c3:04:94:15:7f:53:f6:57:bf:9f:89:b4:ea:6c:8b:16'
         ':35:1f:d7:ec:25:8d:55:6f:82:10:40'),
        RESULT['cert']['sha256_fingerprint'])


def test_has_json_version_section():
    assert_in('json_version', RESULT)
    assert_equal(
        set([
            'serial_number',
            'expiry_datetime',
        ]),
        set(json.loads(RESULT['json_version']).keys()))
