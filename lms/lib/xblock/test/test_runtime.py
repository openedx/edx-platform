"""
Tests of the LMS XBlock Runtime and associated utilities
"""

from ddt import ddt, data
from mock import Mock
from unittest import TestCase
from urlparse import urlparse
from lms.lib.xblock.runtime import quote_slashes, unquote_slashes, LmsModuleSystem

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
        self.assertEquals(test_string, unquote_slashes(quote_slashes(test_string)))

    @data(*TEST_STRINGS)
    def test_escaped(self, test_string):
        self.assertNotIn('/', quote_slashes(test_string))


class TestHandlerUrl(TestCase):
    """Test the LMS handler_url"""

    def setUp(self):
        self.block = Mock()
        self.course_id = "org/course/run"
        self.runtime = LmsModuleSystem(
            static_url='/static',
            track_function=Mock(),
            get_module=Mock(),
            render_template=Mock(),
            replace_urls=str,
            course_id=self.course_id,
            descriptor_runtime=Mock(),
        )

    def test_trailing_characters(self):
        self.assertFalse(self.runtime.handler_url(self.block, 'handler').endswith('?'))
        self.assertFalse(self.runtime.handler_url(self.block, 'handler').endswith('/'))

        self.assertFalse(self.runtime.handler_url(self.block, 'handler', 'suffix').endswith('?'))
        self.assertFalse(self.runtime.handler_url(self.block, 'handler', 'suffix').endswith('/'))

        self.assertFalse(self.runtime.handler_url(self.block, 'handler', 'suffix', 'query').endswith('?'))
        self.assertFalse(self.runtime.handler_url(self.block, 'handler', 'suffix', 'query').endswith('/'))

        self.assertFalse(self.runtime.handler_url(self.block, 'handler', query='query').endswith('?'))
        self.assertFalse(self.runtime.handler_url(self.block, 'handler', query='query').endswith('/'))

    def _parsed_query(self, query_string):
        """Return the parsed query string from a handler_url generated with the supplied query_string"""
        return urlparse(self.runtime.handler_url(self.block, 'handler', query=query_string)).query

    def test_query_string(self):
        self.assertIn('foo=bar', self._parsed_query('foo=bar'))
        self.assertIn('foo=bar&baz=true', self._parsed_query('foo=bar&baz=true'))
        self.assertIn('foo&bar&baz', self._parsed_query('foo&bar&baz'))

    def _parsed_path(self, handler_name='handler', suffix=''):
        """Return the parsed path from a handler_url with the supplied handler_name and suffix"""
        return urlparse(self.runtime.handler_url(self.block, handler_name, suffix=suffix)).path

    def test_suffix(self):
        self.assertTrue(self._parsed_path(suffix="foo").endswith('foo'))
        self.assertTrue(self._parsed_path(suffix="foo/bar").endswith('foo/bar'))
        self.assertTrue(self._parsed_path(suffix="/foo/bar").endswith('/foo/bar'))

    def test_handler_name(self):
        self.assertIn('handler1', self._parsed_path('handler1'))
        self.assertIn('handler_a', self._parsed_path('handler_a'))
