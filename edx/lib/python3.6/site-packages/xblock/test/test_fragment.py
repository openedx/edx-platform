"""
Unit tests for the Fragment class.

Note: this class has been deprecated in favor of web_fragments.fragment.Fragment
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

from xblock.fragment import Fragment


class TestFragment(TestCase):
    """
    Unit tests for fragments.
    """
    def test_fragment(self):
        """
        Test the delegated Fragment class.
        """
        TEST_HTML = u'<p>Hello, world!</p>'  # pylint: disable=invalid-name
        fragment = Fragment()
        fragment.add_content(TEST_HTML)
        self.assertEqual(fragment.body_html(), TEST_HTML)
