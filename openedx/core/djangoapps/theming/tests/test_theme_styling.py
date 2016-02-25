"""
    Tests for comprehensive themes.
"""
import unittest

from django.conf import settings
from django.test import TestCase
from django.contrib import staticfiles

from mock import patch
from paver.easy import call_task

from openedx.core.djangoapps.theming.test_util import with_comprehensive_theme

from pavelib import assets


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
        self.addCleanup(self.clean_up)

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @classmethod
    def setUpClass(cls):
        """
        Enable Comprehensive theme and compile sass files.
        """
        # Apply Comprehensive theme and compile sass assets.
        with patch("pavelib.assets.Env.env_tokens", {'COMPREHENSIVE_THEME_DIR': settings.TEST_THEME}):
            # Configure path for themes
            assets.configure_paths()
            compile_sass('lms')

        super(TestComprehensiveThemeLMS, cls).setUpClass()

    def clean_up(self):
        """
        Disable comprehensive theme and clear changes made for comprehensive themes.
        """
        patch("pavelib.assets.Env.env_tokens", {'COMPREHENSIVE_THEME_DIR': ""})
        clear_theme_sass_dirs()

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_green_footer(self):
        """
        Test that theme footer is used instead of default footer.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        # This string comes from header.html of test-theme
        self.assertContains(resp, "This is a footer for test-theme.")

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_staticfiles_search_path(self):
        """
        Test that static files finders are adjusted according to the applied comprehensive theme.
        """
        # Test that theme Static files directory is added to the start of STATIC_FILES_DIRS list
        self.assertEqual(settings.STATICFILES_DIRS[0], settings.TEST_THEME / 'lms/static')

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_logo_image(self):
        """
        Test that theme logo is used instead of default logo.
        """
        result = staticfiles.finders.find('images/logo.png')
        self.assertEqual(result, settings.TEST_THEME / 'lms/static/images/logo.png')

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_css_files(self):
        """
        Test that theme sass files are used instead of default sass files.
        """
        result = staticfiles.finders.find('css/lms-main.css')
        self.assertEqual(result, settings.TEST_THEME / "lms/static/css/lms-main.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertIn("background:#00fa00", lms_main_css)


@unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
class TestComprehensiveThemeStudio(TestCase):
    """
    Test html, sass and static file overrides for comprehensive themes.
    """

    def setUp(self):
        """
        Clear static file finders cache and register cleanup methods.
        """
        super(TestComprehensiveThemeStudio, self).setUp()
        self.addCleanup(self.clean_up)

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @classmethod
    def setUpClass(cls):
        """
        Enable Comprehensive theme and compile sass files.
        """
        # Apply Comprehensive theme and compile sass assets.
        with patch("pavelib.assets.Env.env_tokens", {'COMPREHENSIVE_THEME_DIR': settings.TEST_THEME}):
            # Configure path for themes
            assets.configure_paths()
            compile_sass('cms')

        super(TestComprehensiveThemeStudio, cls).setUpClass()

    def clean_up(self):
        """
        Disable comprehensive theme and clear changes made for comprehensive themes.
        """
        patch("pavelib.assets.Env.env_tokens", {'COMPREHENSIVE_THEME_DIR': ""})
        clear_theme_sass_dirs()

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_theme_adjusts_staticfiles_search_path(self):
        """
        Test that static files finders are adjusted according to the applied comprehensive theme.
        """
        # Test that theme Static files directory is added to the start of STATIC_FILES_DIRS list
        self.assertEqual(settings.STATICFILES_DIRS[0], settings.TEST_THEME / 'cms/static')

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_overridden_logo_image(self):
        """
        Test that theme logo is used instead of default logo.
        """
        result = staticfiles.finders.find('images/logo.png')
        self.assertEqual(result, settings.TEST_THEME / 'cms/static/images/logo.png')

    @with_comprehensive_theme(settings.TEST_THEME)
    def test_overridden_css_files(self):
        """
        Test that theme sass files are used instead of default sass.
        """
        result = staticfiles.finders.find('css/studio-main.css')
        self.assertEqual(result, settings.TEST_THEME / "cms/static/css/studio-main.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertIn("background:#00fa00", lms_main_css)


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
        result = staticfiles.finders.find('css/lms-main.css')
        self.assertEqual(result, settings.REPO_ROOT / "lms/static/css/lms-main.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertNotIn("background:#00fa00", lms_main_css)


@unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
class TestComprehensiveThemeDisabledStudio(TestCase):
    """
    Test default html, sass and static file are used when no theme is enabled.
    """

    def setUp(self):
        """
        Clear static file finders cache.
        """
        super(TestComprehensiveThemeDisabledStudio, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @classmethod
    def setUpClass(cls):
        """
        Compile sass files.
        """
        # compile studio sass
        compile_sass('cms')

        super(TestComprehensiveThemeDisabledStudio, cls).setUpClass()

    def test_css(self):
        """
        Test that default css files served when no theme is enabled.
        """
        result = staticfiles.finders.find('css/studio-main.css')
        self.assertEqual(result, settings.REPO_ROOT / "cms/static/css/studio-main.css")

        lms_main_css = ""
        with open(result) as css_file:
            lms_main_css += css_file.read()

        self.assertNotIn("background:#00fa00", lms_main_css)


def clear_theme_sass_dirs():
    """
    Clear THEME dirs from SASS_DIRECTORIES and SASS_LOOKUP_DIRECTORIES so that the next sass compilation
    run does not include directories from previous run.
    """
    assets.SASS_DIRECTORIES["THEME_LMS"] = []
    assets.SASS_DIRECTORIES["THEME_CMS"] = []
    assets.SASS_LOOKUP_DIRECTORIES["THEME_LMS"] = []
    assets.SASS_LOOKUP_DIRECTORIES["THEME_CMS"] = []


def compile_sass(system):
    """
    Process xmodule assets and compile sass files for lms.

    :param system - 'lms' or 'cms', specified the system to compile sass for.
    """
    # Compile system sass files
    call_task('pavelib.assets.update_assets', args=(system, "--settings=test"))
