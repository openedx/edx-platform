"""
Tests for methods defined in builtin_assets.py
"""

from django.conf import settings
from unittest import TestCase
from web_fragments.fragment import Fragment, FragmentResource

from xmodule.util import builtin_assets


class AddCssToFragmentTests(TestCase):
    """
    Tests for add_css_to_fragment.

    We would have liked to also test two additional cases:
    * When a theme is enabled, and add_css_to_fragment is called with a
      theme-overriden Sass file, then a URL to themed CSS is added.
    * When a theme is enabled, but add_css_to_fragment is called with a Sass
      file that the theme doesn't override, then a URL to the original (unthemed)
      CSS is added.
    Unfortunately, under edx-platform tests, settings.STATICFILES_STORAGE does not
    include the ThemeStorage class, so themed URL generation doesn't work.
    """

    def test_absolute_path_raises_value_error(self):
        fragment = Fragment()
        with self.assertRaises(ValueError):
            builtin_assets.add_css_to_fragment(
                fragment,
                "/openedx/edx-platform/xmodule/assets/ProblemBlockDisplay.css",
            )

    def test_not_scss_raises_value_error(self):
        fragment = Fragment()
        with self.assertRaises(ValueError):
            builtin_assets.add_css_to_fragment(
                fragment,
                "vertical/public/js/vertical_student_view.js"
            )

    def test_misspelled_path_raises_not_found(self):
        fragment = Fragment()
        with self.assertRaises(FileNotFoundError):
            builtin_assets.add_css_to_fragment(
                fragment,
                "ProblemBlockDisplayyyy.css",
            )

    def test_happy_path(self):
        fragment = Fragment()
        builtin_assets.add_css_to_fragment(fragment, "ProblemBlockDisplay.css")
        assert fragment.resources[0] == FragmentResource(
            kind='url',
            data=f'{settings.REPO_ROOT}/xmodule/assets/ProblemBlockDisplay.css',
            mimetype='text/css',
            placement='head',
        )
