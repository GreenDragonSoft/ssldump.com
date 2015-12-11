#!/usr/bin/env python

import json
import sys

from collections import OrderedDict

import OpenSSL
from OpenSSL.crypto import FILETYPE_TEXT, FILETYPE_PEM, FILETYPE_ASN1

from parse_certificate import parse_expiry, parse_serial_number


def main(x509_pem_filename):
    with open(x509_pem_filename, 'rb') as f:
        x509 = OpenSSL.crypto.load_certificate(
            FILETYPE_PEM, f.read())

    print(json.dumps(format_response('dummy', 443, x509), indent=4))


def format_response(hostname, port, x509):
    expiry_datetime = parse_expiry(x509)

    FIELDS = OrderedDict([
        ('serial_number', parse_serial_number(x509)),
        ('expiry_datetime', str(expiry_datetime)),
        #  ('expiry_days_remaining', days_remaining),
        #  ('certificate.txt', get_certificate_text_as_utf8(x509)),
        #  ('certificate.pem', get_certificate_pem_as_utf8(x509)),
        #  ('certificate.der', get_certificate_asn1_as_utf8(x509)),
    ])

    command_line_examples = [
        (name.replace('_', '-'), value) for name, value in FIELDS.items()
    ]

    json_version = FIELDS

    return OrderedDict([
        ('request', OrderedDict([
            ('hostname', hostname),
            ('port', port),
        ])),

        ('cert', FIELDS),

        ('command_line_examples', command_line_examples),

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


def get_certificate_asn1_as_utf8(x509):
    octets = OpenSSL.crypto.dump_certificate(FILETYPE_ASN1, x509)
    octet_strings = ['{0:02x}'.format(octet) for octet in octets]

    return ':'.join(octet_strings)


if __name__ == '__main__':
    main(sys.argv[1])
