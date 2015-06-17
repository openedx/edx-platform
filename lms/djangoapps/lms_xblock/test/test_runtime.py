"""
Tests of the LMS XBlock Runtime and associated utilities
"""

from django.contrib.auth.models import User
from django.conf import settings
from ddt import ddt, data
from mock import Mock
from unittest import TestCase
from urlparse import urlparse
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from lms.djangoapps.lms_xblock.runtime import quote_slashes, unquote_slashes, LmsModuleSystem
from xblock.fields import ScopeIds

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
        super(TestHandlerUrl, self).setUp()
        self.block = Mock(name='block', scope_ids=ScopeIds(None, None, None, 'dummy'))
        self.course_key = SlashSeparatedCourseKey("org", "course", "run")
        self.runtime = LmsModuleSystem(
            static_url='/static',
            track_function=Mock(),
            get_module=Mock(),
            render_template=Mock(),
            replace_urls=str,
            course_id=self.course_key,
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

    def test_thirdparty_fq(self):
        """Testing the Fully-Qualified URL returned by thirdparty=True"""
        parsed_fq_url = urlparse(self.runtime.handler_url(self.block, 'handler', thirdparty=True))
        self.assertEqual(parsed_fq_url.scheme, 'https')
        self.assertEqual(parsed_fq_url.hostname, settings.SITE_NAME)

    def test_not_thirdparty_rel(self):
        """Testing the Fully-Qualified URL returned by thirdparty=False"""
        parsed_fq_url = urlparse(self.runtime.handler_url(self.block, 'handler', thirdparty=False))
        self.assertEqual(parsed_fq_url.scheme, '')
        self.assertIsNone(parsed_fq_url.hostname)


class TestUserServiceAPI(TestCase):
    """Test the user service interface"""

    def setUp(self):
        super(TestUserServiceAPI, self).setUp()
        self.course_id = SlashSeparatedCourseKey("org", "course", "run")

        self.user = User(username='runtime_robot', email='runtime_robot@edx.org', password='test', first_name='Robot')
        self.user.save()

        def mock_get_real_user(_anon_id):
            """Just returns the test user"""
            return self.user

        self.runtime = LmsModuleSystem(
            static_url='/static',
            track_function=Mock(),
            get_module=Mock(),
            render_template=Mock(),
            replace_urls=str,
            course_id=self.course_id,
            get_real_user=mock_get_real_user,
            descriptor_runtime=Mock(),
        )
        self.scope = 'course'
        self.key = 'key1'

        self.mock_block = Mock()
        self.mock_block.service_declaration.return_value = 'needs'

    def test_get_set_tag(self):
        # test for when we haven't set the tag yet
        tag = self.runtime.service(self.mock_block, 'user_tags').get_tag(self.scope, self.key)
        self.assertIsNone(tag)

        # set the tag
        set_value = 'value'
        self.runtime.service(self.mock_block, 'user_tags').set_tag(self.scope, self.key, set_value)
        tag = self.runtime.service(self.mock_block, 'user_tags').get_tag(self.scope, self.key)

        self.assertEqual(tag, set_value)

        # Try to set tag in wrong scope
        with self.assertRaises(ValueError):
            self.runtime.service(self.mock_block, 'user_tags').set_tag('fake_scope', self.key, set_value)

        # Try to get tag in wrong scope
        with self.assertRaises(ValueError):
            self.runtime.service(self.mock_block, 'user_tags').get_tag('fake_scope', self.key)
