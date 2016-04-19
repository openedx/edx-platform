"""
    Tests for comprehensive themes.
"""
import unittest

from django.conf import settings
from django.test import TestCase, override_settings
from django.contrib import staticfiles

from paver.easy import call_task

from openedx.core.djangoapps.theming.test_util import with_comprehensive_theme


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestComprehensiveThemeLMS(TestCase):
    """
    Test html, sass and static file overrides for comprehensive themes.
    """

    def setUp(self):
        """
        Clear static file finders cache and register cleanup methods.
        """
        super(TestComprehensiveThemeLMS, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @classmethod
    def setUpClass(cls):
        """
        Enable Comprehensive theme and compile sass files.
        """
        # Apply Comprehensive theme and compile sass assets.
        compile_sass('lms')

        super(TestComprehensiveThemeLMS, cls).setUpClass()

    @override_settings(COMPREHENSIVE_THEME_DIR=settings.TEST_THEME.dirname())
    @with_comprehensive_theme(settings.TEST_THEME.basename())
    def test_footer(self):
        """
        Test that theme footer is used instead of default footer.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        # This string comes from header.html of test-theme
        self.assertContains(resp, "This is a footer for test-theme.")

    @override_settings(COMPREHENSIVE_THEME_DIR=settings.TEST_THEME.dirname())
    @with_comprehensive_theme(settings.TEST_THEME.basename())
    def test_logo_image(self):
        """
        Test that theme logo is used instead of default logo.
        """
        result = staticfiles.finders.find('test-theme/images/logo.png')
        self.assertEqual(result, settings.TEST_THEME / 'lms/static/images/logo.png')

    @override_settings(COMPREHENSIVE_THEME_DIR=settings.TEST_THEME.dirname())
    @with_comprehensive_theme(settings.TEST_THEME.basename())
    def test_css_files(self):
        """
        Test that theme sass files are used instead of default sass files.
        """
        result = staticfiles.finders.find('test-theme/css/lms-main-v1.css')
        self.assertEqual(result, settings.TEST_THEME / "lms/static/css/lms-main-v1.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertIn("background:#00fa00", lms_main_css)


@unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
class TestComprehensiveThemeCMS(TestCase):
    """
    Test html, sass and static file overrides for comprehensive themes.
    """

    def setUp(self):
        """
        Clear static file finders cache and register cleanup methods.
        """
        super(TestComprehensiveThemeCMS, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @classmethod
    def setUpClass(cls):
        """
        Enable Comprehensive theme and compile sass files.
        """
        # Apply Comprehensive theme and compile sass assets.
        compile_sass('cms')

        super(TestComprehensiveThemeCMS, cls).setUpClass()

    @override_settings(COMPREHENSIVE_THEME_DIR=settings.TEST_THEME.dirname())
    @with_comprehensive_theme(settings.TEST_THEME.basename())
    def test_template_override(self):
        """
        Test that theme templates are used instead of default templates.
        """
        resp = self.client.get('/signin')
        self.assertEqual(resp.status_code, 200)
        # This string comes from login.html of test-theme
        self.assertContains(resp, "Login Page override for test-theme.")

    @override_settings(COMPREHENSIVE_THEME_DIR=settings.TEST_THEME.dirname())
    @with_comprehensive_theme(settings.TEST_THEME.basename())
    def test_css_files(self):
        """
        Test that theme sass files are used instead of default sass files.
        """
        result = staticfiles.finders.find('test-theme/css/studio-main-v1.css')
        self.assertEqual(result, settings.TEST_THEME / "cms/static/css/studio-main-v1.css")

        cms_main_css = ""
        with open(result) as css_file:
            cms_main_css += css_file.read()

        self.assertIn("background:#00fa00", cms_main_css)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestComprehensiveThemeDisabledLMS(TestCase):
    """
        Test Sass compilation order and sass overrides for comprehensive themes.
    """

    def setUp(self):
        """
        Clear static file finders cache.
        """
        super(TestComprehensiveThemeDisabledLMS, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @classmethod
    def setUpClass(cls):
        """
        Compile sass files.
        """
        # compile LMS SASS
        compile_sass('lms')

        super(TestComprehensiveThemeDisabledLMS, cls).setUpClass()

    def test_logo(self):
        """
        Test that default logo is picked in case of no comprehensive theme.
        """
        result = staticfiles.finders.find('images/logo.png')
        self.assertEqual(result, settings.REPO_ROOT / 'lms/static/images/logo.png')

    def test_css(self):
        """
        Test that default css files served without comprehensive themes applied.
        """
        result = staticfiles.finders.find('css/lms-main-v1.css')
        self.assertEqual(result, settings.REPO_ROOT / "lms/static/css/lms-main-v1.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertNotIn("background:#00fa00", lms_main_css)


@unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
class TestComprehensiveThemeDisabledCMS(TestCase):
    """
    Test default html, sass and static file when no theme is applied.
    """

    def setUp(self):
        """
        Clear static file finders cache and register cleanup methods.
        """
        super(TestComprehensiveThemeDisabledCMS, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @classmethod
    def setUpClass(cls):
        """
        Enable Comprehensive theme and compile sass files.
        """
        # Apply Comprehensive theme and compile sass assets.
        compile_sass('cms')

        super(TestComprehensiveThemeDisabledCMS, cls).setUpClass()

    def test_template_override(self):
        """
        Test that defaults templates are used when no theme is applied.
        """
        resp = self.client.get('/signin')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Login Page override for test-theme.")

    def test_css_files(self):
        """
        Test that default css files served without comprehensive themes applied..
        """
        result = staticfiles.finders.find('css/studio-main-v1.css')
        self.assertEqual(result, settings.REPO_ROOT / "cms/static/css/studio-main-v1.css")

        cms_main_css = ""
        with open(result) as css_file:
            cms_main_css += css_file.read()

        self.assertNotIn("background:#00fa00", cms_main_css)


def compile_sass(system):
    """
    Process xmodule assets and compile sass files for the given system.

    :param system - 'lms' or 'cms', specified the system to compile sass for.
    """
    # Compile system sass files
    call_task(
        'pavelib.assets.update_assets',
        args=(
            system,
            "--themes_dir={}".format(settings.TEST_THEME.dirname()),
            "--themes={}".format(settings.TEST_THEME.basename()),
            "--settings=test"),
    )
