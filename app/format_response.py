#!/usr/bin/env python

import json
import sys

from collections import OrderedDict

import OpenSSL
from OpenSSL.crypto import FILETYPE_TEXT, FILETYPE_PEM, FILETYPE_ASN1

from parse_certificate import (
    parse_expiry, parse_serial_number, parse_subject_components)


def main(x509_pem_filename):
    with open(x509_pem_filename, 'rb') as f:
        x509 = OpenSSL.crypto.load_certificate(
            FILETYPE_PEM, f.read())

    print(json.dumps(format_response('dummy', 443, x509), indent=4))


def format_response(hostname, port, x509):
    expiry_datetime = parse_expiry(x509)
    subject_components = parse_subject_components(x509)

    FIELDS = OrderedDict([
        ('serial_number', parse_serial_number(x509)),
        ('expiry_datetime', str(expiry_datetime)),
        ('subject_common_name', subject_components.get('common_name')),
        ('subject_organization', subject_components.get('organization')),

        ('subject_organizational_unit',
         subject_components.get('organizational_unit')),

        ('subject_street', subject_components.get('street')),
        ('subject_locality', subject_components.get('locality')),
        ('subject_state', subject_components.get('state')),
        ('subject_postal_code', subject_components.get('postal_code')),
        ('subject_country', subject_components.get('country')),
        ('email_address', subject_components.get('email_address')),

        ('sha1_fingerprint', get_fingerprint(x509, 'sha1')),
        ('sha256_fingerprint', get_fingerprint(x509, 'sha256')),

        #  ('expiry_days_remaining', days_remaining),
        ('certificate.txt', get_certificate_text_as_utf8(x509)),
        ('certificate.pem', get_certificate_pem_as_utf8(x509)),
        ('certificate.der.txt', get_certificate_asn1_as_utf8(x509)),
        ('certificate.der', get_certificate_asn1_as_binary(x509)),
    ])

    json_field_names = ['serial_number', 'expiry_datetime']
    json_version = OrderedDict([(k, FIELDS[k]) for k in json_field_names])

    return OrderedDict([
        ('request', OrderedDict([
            ('hostname', hostname),
            ('port', port),
        ])),

        ('cert', FIELDS),

        ('standard_fields', OrderedDict([
            ('serial_number', 'Serial number'),
            ('expiry_datetime', 'Expiry'),
            ('subject_common_name', 'Common name'),
            ('subject_organization', 'Organization'),
            ('subject_organizational_unit', 'Organizational unit'),
            ('subject_street', 'Street'),
            ('subject_locality', 'Locality'),
            ('subject_state', 'State or province'),
            ('subject_postal_code', 'Postal code'),
            ('subject_country', 'Country'),
            ('email_address', 'Email address'),
            ('sha1_fingerprint', 'SHA1 Fingerprint'),
            ('sha256_fingerprint', 'SHA256 Fingerprint'),
        ])),

        ('json_version', json.dumps(json_version, indent=4)),
    ])


def get_certificate_text_as_utf8(x509):
    string = OpenSSL.crypto.dump_certificate(
        FILETYPE_TEXT, x509).decode('utf-8')
    return string


def get_certificate_pem_as_utf8(x509):
    string = OpenSSL.crypto.dump_certificate(
        FILETYPE_PEM, x509).decode('utf-8')
    return string


def get_certificate_asn1_as_binary(x509):
    return OpenSSL.crypto.dump_certificate(FILETYPE_ASN1, x509)


def get_certificate_asn1_as_utf8(x509):
    octets = bytearray(get_certificate_asn1_as_binary(x509))
    octet_strings = ['{0:02x}'.format(octet) for octet in octets]

    long_line = ':'.join(octet_strings)

    return split_every_n(long_line, 54)


def get_fingerprint(x509, digest_name):
    return x509.digest(digest_name).decode('ascii').lower()  # eg '64:2d:ea...'


def split_every_n(string, n):
    return '\n'.join(
        [string[i:i + n] for i in range(0, len(string), n)])


if __name__ == '__main__':
    main(sys.argv[1])
