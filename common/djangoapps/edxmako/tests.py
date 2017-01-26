
from mock import patch, Mock
import unittest
import ddt

from request_cache.middleware import RequestCache
from django.conf import settings
from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from edxmako.request_context import get_template_request_context
from edxmako import add_lookup, LOOKUP
from edxmako.shortcuts import (
    marketing_link,
    is_marketing_link_set,
    is_any_marketing_link_set,
    render_to_string,
)
from student.tests.factories import UserFactory
from util.testing import UrlResetMixin


@ddt.ddt
class ShortcutsTests(UrlResetMixin, TestCase):
    """
    Test the edxmako shortcuts file
    """
    @override_settings(MKTG_URLS={'ROOT': 'dummy-root', 'ABOUT': '/about-us'})
    @override_settings(MKTG_URL_LINK_MAP={'ABOUT': 'login'})
    def test_marketing_link(self):
        # test marketing site on
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            expected_link = 'dummy-root/about-us'
            link = marketing_link('ABOUT')
            self.assertEquals(link, expected_link)
        # test marketing site off
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': False}):
            # we are using login because it is common across both cms and lms
            expected_link = reverse('login')
            link = marketing_link('ABOUT')
            self.assertEquals(link, expected_link)

    @override_settings(MKTG_URLS={'ROOT': 'dummy-root', 'ABOUT': '/about-us'})
    @override_settings(MKTG_URL_LINK_MAP={'ABOUT': 'login'})
    def test_is_marketing_link_set(self):
        # test marketing site on
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.assertTrue(is_marketing_link_set('ABOUT'))
            self.assertFalse(is_marketing_link_set('NOT_CONFIGURED'))
        # test marketing site off
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': False}):
            self.assertTrue(is_marketing_link_set('ABOUT'))
            self.assertFalse(is_marketing_link_set('NOT_CONFIGURED'))

    @override_settings(MKTG_URLS={'ROOT': 'dummy-root', 'ABOUT': '/about-us'})
    @override_settings(MKTG_URL_LINK_MAP={'ABOUT': 'login'})
    def test_is_any_marketing_link_set(self):
        # test marketing site on
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.assertTrue(is_any_marketing_link_set(['ABOUT']))
            self.assertTrue(is_any_marketing_link_set(['ABOUT', 'NOT_CONFIGURED']))
            self.assertFalse(is_any_marketing_link_set(['NOT_CONFIGURED']))
        # test marketing site off
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': False}):
            self.assertTrue(is_any_marketing_link_set(['ABOUT']))
            self.assertTrue(is_any_marketing_link_set(['ABOUT', 'NOT_CONFIGURED']))
            self.assertFalse(is_any_marketing_link_set(['NOT_CONFIGURED']))


class AddLookupTests(TestCase):
    """
    Test the `add_lookup` function.
    """
    @patch('edxmako.LOOKUP', {})
    def test_with_package(self):
        add_lookup('test', 'management', __name__)
        dirs = LOOKUP['test'].directories
        self.assertEqual(len(dirs), 1)
        self.assertTrue(dirs[0].endswith('management'))


class MakoRequestContextTest(TestCase):
    """
    Test MakoMiddleware.
    """

    def setUp(self):
        super(MakoRequestContextTest, self).setUp()
        self.user = UserFactory.create()
        self.url = "/"
        self.request = RequestFactory().get(self.url)
        self.request.user = self.user
        self.response = Mock(spec=HttpResponse)

        self.addCleanup(RequestCache.clear_request_cache)

    def test_with_current_request(self):
        """
        Test that if get_current_request returns a request, then get_template_request_context
        returns a RequestContext.
        """

        with patch('edxmako.request_context.get_current_request', return_value=self.request):
            # requestcontext should not be None.
            self.assertIsNotNone(get_template_request_context())

    def test_without_current_request(self):
        """
        Test that if get_current_request returns None, then get_template_request_context
        returns None.
        """
        with patch('edxmako.request_context.get_current_request', return_value=None):
            # requestcontext should be None.
            self.assertIsNone(get_template_request_context())

    def test_request_context_caching(self):
        """
        Test that the RequestContext is cached in the RequestCache.
        """
        with patch('edxmako.request_context.get_current_request', return_value=None):
            # requestcontext should be None, because the cache isn't filled
            self.assertIsNone(get_template_request_context())

        with patch('edxmako.request_context.get_current_request', return_value=self.request):
            # requestcontext should not be None, and should fill the cache
            self.assertIsNotNone(get_template_request_context())

        mock_get_current_request = Mock()
        with patch('edxmako.request_context.get_current_request', mock_get_current_request):
            # requestcontext should not be None, because the cache is filled
            self.assertIsNotNone(get_template_request_context())
        mock_get_current_request.assert_not_called()

        RequestCache.clear_request_cache()

        with patch('edxmako.request_context.get_current_request', return_value=None):
            # requestcontext should be None, because the cache isn't filled
            self.assertIsNone(get_template_request_context())

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_render_to_string_when_no_global_context_lms(self):
        """
        Test render_to_string() when makomiddleware has not initialized
        the threadlocal REQUEST_CONTEXT.context. This is meant to run in LMS.
        """
        self.assertIn("this module is temporarily unavailable", render_to_string("courseware/error-message.html", None))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
    def test_render_to_string_when_no_global_context_cms(self):
        """
        Test render_to_string() when makomiddleware has not initialized
        the threadlocal REQUEST_CONTEXT.context. This is meant to run in CMS.
        """
        self.assertIn("We're having trouble rendering your component", render_to_string("html_error.html", None))
