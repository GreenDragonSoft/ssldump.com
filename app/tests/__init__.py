from os.path import dirname, join as pjoin

import OpenSSL


def load_example_x509():
    filename = pjoin(dirname(__file__), 'sample_data', 'example.com.pem')
    with open(filename, 'rb') as f:
        return OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, f.read())
