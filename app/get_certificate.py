#!/usr/bin/env python

from __future__ import unicode_literals

import logging
import socket
import sys

import OpenSSL


LOG = logging.getLogger(__name__)


def main(hostname):
    logging.basicConfig(level=logging.DEBUG)
    x509 = get_certificate(hostname, 443)

    for filetype, extension in [
            (OpenSSL.crypto.FILETYPE_PEM, 'pem'),
            (OpenSSL.crypto.FILETYPE_TEXT, 'txt'),
            (OpenSSL.crypto.FILETYPE_ASN1, 'asn1')]:

        filename = '{}.{}'.format(hostname, extension)
        with open(filename, 'wb') as f:
            b = OpenSSL.crypto.dump_certificate(filetype, x509)
            f.write(b)

        print('Wrote out {}'.format(filename))


def get_certificate(hostname, port):
    LOG.info('Getting {} on port {}'.format(hostname, port))

    try:
        x509 = download_certificate_for(hostname, port)
    except Exception as e:
        LOG.exception(e)
        raise

    return x509


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


if __name__ == '__main__':
    main(sys.argv[1])
