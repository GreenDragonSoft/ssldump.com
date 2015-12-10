from __future__ import unicode_literals

import datetime
import logging
import re
import socket

from collections import OrderedDict

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


def parse_expiry(x509):
    return parse_date_field(x509.get_notAfter())


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
    cert = connection.get_peer_certificate()  # Returns OpenSSL.crypto.X509

    return cert


def parse_date_field(date_field):
    """
    Return a utcdatetime from `datetime_field`, which is of one of the
    following formats:

    YYYYMMDDhhmmssZ
    YYYYMMDDhhmmss+hhmm
    YYYYMMDDhhmmss-hhmm

    See http://pyopenssl.sourceforge.net/pyOpenSSL.html/openssl-x509.html
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
