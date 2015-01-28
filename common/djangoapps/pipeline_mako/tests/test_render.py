"""Tests for rendering functions in the mako pipeline. """

from django.test import TestCase
from pipeline_mako import render_require_js_path_overrides, require_js_path


class RequireJSPathOverridesTest(TestCase):
    """Test RequireJS path overrides. """

    OVERRIDES = {
        'jquery': 'js/vendor/jquery.min.js',
        'backbone': 'js/vendor/backbone-min.js',
        'text': 'js/vendor/text.js'
    }

    OVERRIDES_JS = (
        "<script type=\"text/javascript\">\n"
        "var require = require || {};\n"
        "require.paths = require.paths || [];\n"
        "require.baseUrl = '/static/'\n"
        "require.paths['jquery'] = 'js/vendor/jquery.min';\n"
        "require.paths['text'] = 'js/vendor/text';\n"
        "require.paths['backbone'] = 'js/vendor/backbone-min';\n"
        "</script>"
    )

    def test_requirejs_path_overrides(self):
        result = render_require_js_path_overrides(self.OVERRIDES)
        self.assertEqual(result, self.OVERRIDES_JS)


class RequireJSPathTest(TestCase):
    """Test `require_js_path` method. """

    def test_require_js_path(self):
        result = require_js_path('js/vendor/jquery.min.js')
        self.assertEqual(result, 'js/vendor/jquery.min')
