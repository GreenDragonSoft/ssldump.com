#!/usr/bin/env python

from __future__ import unicode_literals

import datetime
import logging
import re
import socket
import sys

from collections import OrderedDict
from pprint import pprint

import utcdatetime
import OpenSSL

from iso8601 import parse_date as parse_datetime

LOG = logging.getLogger(__name__)

COMPONENT_NAMES = {
    'CN': 'common_name',
    'C': 'country',
    'ST': 'state',
    'L': 'locality',
    'O': 'organisation',
    'street': 'street',
    'postalCode': 'postal_code',
    'businessCategory': 'business_category',
}


def main(hostname):
    logging.basicConfig(level=logging.DEBUG)
    pprint(get_certificate(hostname, 443))


def get_certificate_expiry(hostname, port):
    x509 = get_certificate(hostname, port)
    return parse_date_field(x509.get_notAfter())


def get_certificate(hostname, port):
    LOG.info('Getting {} on port {}'.format(hostname, port))

    try:
        x509 = download_certificate_for(hostname, port)
    except Exception as e:
        LOG.exception(e)
        raise

    return x509


def decode_certificate(x509):
    certificate = OrderedDict()
    certificate['expires'] = parse_date_field(x509.get_notAfter())

    for key, value in x509.get_subject().get_components():
        key, value = key.decode('utf-8'), value.decode('utf-8')
        try:
            long_name = COMPONENT_NAMES[key]
        except KeyError:
            LOG.warn('Skipping component `{}` = `{}`'.format(key, value))
            continue
        else:
            certificate[long_name] = value

    utc_now = datetime.datetime.now(certificate['expires'].tzinfo)

    LOG.info('Expires in {}'.format(certificate['expires'] - utc_now))
    return certificate


def download_certificate_for(hostname, port):
    def some_callback(connection, cert, error_number, error_depth, ok):
        LOG.debug('connection: {}, cert: {}, error_number: {}, '
                  'error_depth: {} ok: {}'.format(
                      connection, cert, error_number, error_depth, ok))

    ssl_context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)
    ssl_context.set_verify(OpenSSL.SSL.VERIFY_NONE, callback=some_callback)

    s = socket.socket()

    connection = OpenSSL.SSL.Connection(ssl_context, s)
    connection.set_tlsext_host_name(hostname.encode('ascii'))  # for SNI
    connection.connect((hostname, port))
    connection.do_handshake()
    cert = connection.get_peer_certificate()

    return cert


def parse_date_field(date_field):
    """
    >>> parse_date_field(b'20161029235959Z')
    datetime.datetime(2016, 10, 29, 23, 59, 59, tzinfo=<UTC>)
    >>> parse_date_field(b'20161029235959+0100')
    datetime.datetime(2016, 10, 29, 22, 59, 59, tzinfo=<UTC>)
    >>> parse_date_field(b'20161029235959+0100')
    datetime.datetime(2016, 10, 30, 00, 59, 59, tzinfo=<UTC>)
    """
    match = re.match(
        '(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})'
        '(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'
        '(?P<timezone>[+-]\d{4}|Z)', date_field.decode('utf-8'))

    isodate = '{}-{}-{}T{}:{}:{}{}'.format(
        match.group('year'),
        match.group('month'),
        match.group('day'),
        match.group('hour'),
        match.group('minute'),
        match.group('second'),
        match.group('timezone'))

    return utcdatetime.utcdatetime.from_datetime(parse_datetime(isodate))

if __name__ == '__main__':
    main(sys.argv[1])
