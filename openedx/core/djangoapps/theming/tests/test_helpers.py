"""Tests of comprehensive theming."""
import unittest
from mock import patch

from django.test import TestCase, RequestFactory
from django.conf import settings

from openedx.core.djangoapps.theming.test_util import with_comprehensive_theme
from openedx.core.djangoapps.theming.helpers import get_template_path_with_theme, strip_site_theme_templates_path, \
    get_current_site_theme_dir


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestHelpersLMS(TestCase):
    """Test comprehensive theming helper functions."""

    def setUp(self):
        super(TestHelpersLMS, self).setUp()

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_enabled(self):
        """
        Tests template paths are returned from enabled theme.
        """
        template_path = get_template_path_with_theme('header.html')
        self.assertEqual(template_path, '/red-theme/lms/templates/header.html')

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_for_missing_template(self):
        """
        Tests default template paths are returned if template is not found in the theme.
        """
        template_path = get_template_path_with_theme('course.html')
        self.assertEqual(template_path, 'course.html')

    def test_get_template_path_with_theme_disabled(self):
        """
        Tests default template paths are returned when theme is non theme is enabled.
        """
        template_path = get_template_path_with_theme('header.html')
        self.assertEqual(template_path, 'header.html')

    @with_comprehensive_theme('red-theme')
    def test_strip_site_theme_templates_path_theme_enabled(self):
        """
        Tests site theme templates path is stripped from the given template path.
        """
        template_path = strip_site_theme_templates_path('/red-theme/lms/templates/header.html')
        self.assertEqual(template_path, 'header.html')

    def test_strip_site_theme_templates_path_theme_disabled(self):
        """
        Tests site theme templates path returned unchanged if no theme is applied.
        """
        template_path = strip_site_theme_templates_path('/red-theme/lms/templates/header.html')
        self.assertEqual(template_path, '/red-theme/lms/templates/header.html')

    @with_comprehensive_theme('red-theme')
    def test_get_current_site_theme_dir(self):
        """
        Tests current site theme name.
        """
        factory = RequestFactory()
        with patch(
            'edxmako.middleware.REQUEST_CONTEXT.request',
            factory.get('/', SERVER_NAME="red-theme.org"),
            create=True,
        ):
            current_site = get_current_site_theme_dir()
            self.assertEqual(current_site, 'red-theme')


@unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
class TestHelpersCMS(TestCase):
    """Test comprehensive theming helper functions."""

    def setUp(self):
        super(TestHelpersCMS, self).setUp()

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_enabled(self):
        """
        Tests template paths are returned from enabled theme.
        """
        template_path = get_template_path_with_theme('login.html')
        self.assertEqual(template_path, '/red-theme/cms/templates/login.html')

    @with_comprehensive_theme('red-theme')
    def test_get_template_path_with_theme_for_missing_template(self):
        """
        Tests default template paths are returned if template is not found in the theme.
        """
        template_path = get_template_path_with_theme('certificates.html')
        self.assertEqual(template_path, 'certificates.html')

    def test_get_template_path_with_theme_disabled(self):
        """
        Tests default template paths are returned when theme is non theme is enabled.
        """
        template_path = get_template_path_with_theme('login.html')
        self.assertEqual(template_path, 'login.html')

    @with_comprehensive_theme('red-theme')
    def test_strip_site_theme_templates_path_theme_enabled(self):
        """
        Tests site theme templates path is stripped from the given template path.
        """
        template_path = strip_site_theme_templates_path('/red-theme/cms/templates/login.html')
        self.assertEqual(template_path, 'login.html')

    def test_strip_site_theme_templates_path_theme_disabled(self):
        """
        Tests site theme templates path returned unchanged if no theme is applied.
        """
        template_path = strip_site_theme_templates_path('/red-theme/cms/templates/login.html')
        self.assertEqual(template_path, '/red-theme/cms/templates/login.html')

    @with_comprehensive_theme('red-theme')
    def test_get_current_site_theme_dir(self):
        """
        Tests current site theme name.
        """
        factory = RequestFactory()
        with patch(
            'edxmako.middleware.REQUEST_CONTEXT.request',
            factory.get('/', SERVER_NAME="red-theme.org"),
            create=True,
        ):
            current_site = get_current_site_theme_dir()
            self.assertEqual(current_site, 'red-theme')
