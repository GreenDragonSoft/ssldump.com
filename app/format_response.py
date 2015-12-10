#!/usr/bin/env python

import json
import sys

from collections import OrderedDict

import OpenSSL

from parse_certificate import parse_expiry


def main(x509_pem_filename):
    with open(x509_pem_filename, 'rb') as f:
        x509 = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, f.read())

    print(json.dumps(format_response('dummy', 443, x509), indent=4))


def format_response(hostname, port, x509):
    return OrderedDict([
        ('request', OrderedDict([
            ('hostname', hostname),
            ('port', port),
        ])),
        ('certificate_expiry',
         str(parse_expiry(x509))),
    ])


if __name__ == '__main__':
    main(sys.argv[1])
