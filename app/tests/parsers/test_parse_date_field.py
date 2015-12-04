from nose.tools import assert_equal

from utcdatetime import utcdatetime

from get_certificate import parse_date_field


def test_parse_date_field():
    yield (_assert_date_parsed_as,
           utcdatetime(2016, 10, 29, 23, 59, 59),
           b'20161029235959Z')

    yield (_assert_date_parsed_as,
           utcdatetime(2016, 10, 29, 22, 59, 59),
           b'20161029235959+0100')

    yield (_assert_date_parsed_as,
           utcdatetime(2016, 10, 30, 5, 59, 59),
           b'20161029235959-0600')


def _assert_date_parsed_as(expected, binary_date_field):
    assert_equal(expected, parse_date_field(binary_date_field))
