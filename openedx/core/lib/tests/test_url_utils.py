"""
Tests for url_utils module.
"""

from ddt import data, ddt
from django.test import TestCase

from openedx.core.lib.url_utils import quote_slashes, unquote_slashes

TEST_STRINGS = [
    '',
    'foobar',
    'foo/bar',
    'foo/bar;',
    'foo;;bar',
    'foo;_bar',
    'foo/',
    '/bar',
    'foo//bar',
    'foo;;;bar',
]


@ddt
class TestQuoteSlashes(TestCase):
    """Test the quote_slashes and unquote_slashes functions"""

    @data(*TEST_STRINGS)
    def test_inverse(self, test_string):
        self.assertEqual(test_string, unquote_slashes(quote_slashes(test_string)))

    @data(*TEST_STRINGS)
    def test_escaped(self, test_string):
        self.assertNotIn('/', quote_slashes(test_string))
