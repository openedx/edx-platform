"""Tests of comprehensive theming."""

import unittest
from django.conf import settings
from django.test import TestCase

from path import path           # pylint: disable=no-name-in-module
from django.contrib import staticfiles

from openedx.core.djangoapps.theming.test_util import with_comp_theme
from openedx.core.lib.tempdir import mkdtemp_clean


class TestComprehensiveTheming(TestCase):
    """Test comprehensive theming."""

    def setUp(self):
        super(TestComprehensiveTheming, self).setUp()

        # Clear the internal staticfiles caches, to get test isolation.
        staticfiles.finders.get_finder.cache_clear()

    @with_comp_theme(settings.REPO_ROOT / 'themes/red-theme')
    @unittest.skip("Disabled until we can release theming to production")
    def test_red_footer(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        # This string comes from footer.html
        self.assertContains(resp, "super-ugly")
        # This string comes from header.html
        self.assertContains(resp, "This file is only for demonstration, and is horrendous!")

    def test_theme_outside_repo(self):
        # Need to create a temporary theme, and defer decorating the function
        # until it is done, which leads to this strange nested-function style
        # of test.

        # Make a temp directory as a theme.
        tmp_theme = path(mkdtemp_clean())
        template_dir = tmp_theme / "lms/templates"
        template_dir.makedirs()
        with open(template_dir / "footer.html", "w") as footer:
            footer.write("<footer>TEMPORARY THEME</footer>")

        @with_comp_theme(tmp_theme)
        def do_the_test(self):
            """A function to do the work so we can use the decorator."""
            resp = self.client.get('/')
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, "TEMPORARY THEME")

        do_the_test(self)

    def test_theme_adjusts_staticfiles_search_path(self):
        # Test that a theme adds itself to the staticfiles search path.
        before_finders = list(settings.STATICFILES_FINDERS)
        before_dirs = list(settings.STATICFILES_DIRS)

        @with_comp_theme(settings.REPO_ROOT / 'themes/red-theme')
        def do_the_test(self):
            """A function to do the work so we can use the decorator."""
            self.assertEqual(list(settings.STATICFILES_FINDERS), before_finders)
            self.assertEqual(settings.STATICFILES_DIRS[0], settings.REPO_ROOT / 'themes/red-theme/lms/static')
            self.assertEqual(settings.STATICFILES_DIRS[1:], before_dirs)

        do_the_test(self)

    @unittest.skip("Disabled until we can release theming to production")
    def test_default_logo_image(self):
        result = staticfiles.finders.find('images/logo.png')
        self.assertEqual(result, settings.REPO_ROOT / 'lms/static/images/logo.png')

    @with_comp_theme(settings.REPO_ROOT / 'themes/red-theme')
    def test_overridden_logo_image(self):
        result = staticfiles.finders.find('images/logo.png')
        self.assertEqual(result, settings.REPO_ROOT / 'themes/red-theme/lms/static/images/logo.png')
