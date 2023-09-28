"""
Tests of pipeline_mako/templates/static_content.html
"""


import unittest

from common.djangoapps.edxmako.shortcuts import render_to_string


class TestStaticContent(unittest.TestCase):
    """Tests for static_content.html"""

    def test_optional_include_mako(self):
        out = render_to_string("test_optional_include_mako.html", {})
        assert 'Welcome to test_optional_include_mako.html' in out
        assert 'This is test_exists.html' in out
