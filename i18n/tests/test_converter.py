import os
from unittest import TestCase

import converter

class UpcaseConverter(converter.Converter):
    """
    Converts a string to uppercase. Just used for testing.
    """
    def inner_convert_string(self, string):
        return string.upper()


class TestConverter(TestCase):
    """
    Tests functionality of i18n/converter.py
    """

    def test_converter(self):
        """
        Tests with a simple converter (converts strings to uppercase).
        Assert that embedded HTML and python tags are not converted.
        """
        c = UpcaseConverter()
        test_cases = [
            # no tags
            ('big bad wolf', 'BIG BAD WOLF'),
            # one html tag
            ('big <strong>bad</strong> wolf', 'BIG <strong>BAD</strong> WOLF'),
            # two html tags
            ('big <b>bad</b> <i>wolf</i>', 'BIG <b>BAD</b> <i>WOLF</i>'),
            # html tags with attributes
            ('<a href="foo">bar</a> baz', '<a href="foo">BAR</a> BAZ'),
            ("<a href='foo'>bar</a> baz", "<a href='foo'>BAR</a> BAZ"),
            # one python tag
            ('big %(adjective)s wolf', 'BIG %(adjective)s WOLF'),
            # two python tags
            ('big %(adjective)s %(noun)s', 'BIG %(adjective)s %(noun)s'),
            # both kinds of tags
            ('<strong>big</strong> %(adjective)s %(noun)s',
             '<strong>BIG</strong> %(adjective)s %(noun)s'),
            # .format-style tags
            ('The {0} barn is {1!r}.', 'THE {0} BARN IS {1!r}.'),
            # HTML entities
            ('<b>&copy; 2013 edX, &#xa0;</b>', '<b>&copy; 2013 EDX, &#xa0;</b>'),
        ]
        for source, expected in test_cases:
            result = c.convert(source)
            self.assertEquals(result, expected)
