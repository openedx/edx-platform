"""Tests of i18n/converter.py"""

from unittest import TestCase

import ddt

from i18n import converter

class UpcaseConverter(converter.Converter):
    """
    Converts a string to uppercase. Just used for testing.
    """
    def inner_convert_string(self, string):
        return string.upper()


@ddt.ddt
class TestConverter(TestCase):
    """
    Tests functionality of i18n/converter.py
    """

    @ddt.data(
        # no tags
        ('big bad wolf',
         'BIG BAD WOLF'),
        # one html tag
        ('big <strong>bad</strong> wolf',
         'BIG <strong>BAD</strong> WOLF'),
        # two html tags
        ('big <b>bad</b> gray <i>wolf</i>',
         'BIG <b>BAD</b> GRAY <i>WOLF</i>'),
        # html tags with attributes
        ('<a href="foo">bar</a> baz',
         '<a href="foo">BAR</a> BAZ'),
        ("<a href='foo'>bar</a> baz",
         "<a href='foo'>BAR</a> BAZ"),
        # one python tag
        ('big %(adjective)s wolf',
         'BIG %(adjective)s WOLF'),
        # two python tags
        ('big %(adjective)s gray %(noun)s',
         'BIG %(adjective)s GRAY %(noun)s'),
        # both kinds of tags
        ('<strong>big</strong> %(adjective)s %(noun)s',
         '<strong>BIG</strong> %(adjective)s %(noun)s'),
        # .format-style tags
        ('The {0} barn is {1!r}.',
         'THE {0} BARN IS {1!r}.'),
        # HTML entities
        ('<b>&copy; 2013 edX, &#xa0;</b>',
         '<b>&copy; 2013 EDX, &#xa0;</b>'),
    )
    def test_converter(self, data):
        """
        Tests with a simple converter (converts strings to uppercase).
        Assert that embedded HTML and python tags are not converted.
        """
        source, expected = data
        result = UpcaseConverter().convert(source)
        self.assertEquals(result, expected)
