""" Tests for rendering functions in the mako pipeline. """

from django.test import TestCase
from pipeline_mako import render_require_js_path_overrides


class RequireJSPathOverridesTest(TestCase):
    """Test RequireJS path overrides. """

    OVERRIDES = [
        'js/vendor/jquery.min.js',
        'js/vendor/backbone-min.js',
        'js/vendor/text.js'
    ]

    OVERRIDES_JS = [
        "<script type=\"text/javascript\">",
        "(function (require) {",
        "require.config({",
        "paths: {",
        "'js/vendor/jquery.min': 'js/vendor/jquery.min',",
        "'js/vendor/backbone-min': 'js/vendor/backbone-min',",
        "'js/vendor/text': 'js/vendor/text'",
        "}",
        "});",
        "}).call(this, require || RequireJS.require);",
        "</script>"
    ]

    def test_requirejs_path_overrides(self):
        result = render_require_js_path_overrides(self.OVERRIDES)
        # To make the string comparision easy remove the whitespaces
        self.assertEqual(map(str.strip, result.splitlines()), self.OVERRIDES_JS)
