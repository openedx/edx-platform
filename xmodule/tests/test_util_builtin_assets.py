"""
Tests for methods defined in builtin_assets.py
"""
from unittest import TestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from web_fragments.fragment import Fragment, FragmentResource

from xmodule.util import builtin_assets


<<<<<<< HEAD
class AddSassToFragmentTests(TestCase):
    """
    Tests for add_sass_to_fragment.

    We would have liked to also test two additional cases:
    * When a theme is enabled, and add_sass_to_fragment is called with a
      theme-overriden Sass file, then a URL to themed CSS is added.
    * When a theme is enabled, but add_sass_to_fragment is called with a Sass
      file that the theme doesn't override, then a URL to the original (unthemed)
      CSS is added.
    Unfortunately, under edx-platform tests, settings.STATICFILES_STORAGE does not
    include the ThemeStorage class, so themed URL generation doesn't work.
=======
class AddCssToFragmentTests(TestCase):
    """
    Tests for add_css_to_fragment.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """

    def test_absolute_path_raises_value_error(self):
        fragment = Fragment()
        with self.assertRaises(ValueError):
<<<<<<< HEAD
            builtin_assets.add_sass_to_fragment(
                fragment,
                "/openedx/edx-platform/xmodule/assets/ProblemBlockDisplay.scss",
            )

    def test_not_scss_raises_value_error(self):
        fragment = Fragment()
        with self.assertRaises(ValueError):
            builtin_assets.add_sass_to_fragment(
=======
            builtin_assets.add_css_to_fragment(
                fragment,
                "/openedx/edx-platform/xmodule/assets/VideoBlockEditor.css",
            )

    def test_not_css_raises_value_error(self):
        fragment = Fragment()
        with self.assertRaises(ValueError):
            builtin_assets.add_css_to_fragment(
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                fragment,
                "vertical/public/js/vertical_student_view.js"
            )

    def test_misspelled_path_raises_not_found(self):
        fragment = Fragment()
        with self.assertRaises(FileNotFoundError):
<<<<<<< HEAD
            builtin_assets.add_sass_to_fragment(
                fragment,
                "ProblemBlockDisplayyyy.scss",
=======
            builtin_assets.add_css_to_fragment(
                fragment,
                "VideoBlockEditorrrrr.css",
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            )

    def test_static_file_missing_raises_improperly_configured(self):
        fragment = Fragment()
        with patch.object(builtin_assets, 'get_static_file_url', lambda _path: None):
            with self.assertRaises(ImproperlyConfigured):
<<<<<<< HEAD
                builtin_assets.add_sass_to_fragment(
                    fragment,
                    "ProblemBlockDisplay.scss",
=======
                builtin_assets.add_css_to_fragment(
                    fragment,
                    "VideoBlockEditor.css",
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                )

    def test_happy_path(self):
        fragment = Fragment()
<<<<<<< HEAD
        builtin_assets.add_sass_to_fragment(fragment, "ProblemBlockDisplay.scss")
        assert fragment.resources[0] == FragmentResource(
            kind='url',
            data='/static/css/ProblemBlockDisplay.css',
=======
        builtin_assets.add_css_to_fragment(fragment, "VideoBlockEditor.css")
        assert fragment.resources[0] == FragmentResource(
            kind='url',
            data='/static/css-builtin-blocks/VideoBlockEditor.css',
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            mimetype='text/css',
            placement='head',
        )
