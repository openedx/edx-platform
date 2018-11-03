#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example fragment view.
"""

from __future__ import absolute_import, unicode_literals

from web_fragments.fragment import Fragment
from web_fragments.test_utils import TEST_CSS, TEST_HTML, TEST_JS
from web_fragments.views import FragmentView

EXAMPLE_FRAGMENT_VIEW_NAME = 'example_fragment_view'


class ExampleFragmentView(FragmentView):
    """
    Simple fragment view for testing.
    """

    def render_to_fragment(self, request, **kwargs):
        """
        Returns a simple fragment
        """
        fragment = Fragment(TEST_HTML)
        fragment.add_javascript(TEST_JS)
        fragment.add_css(TEST_CSS)
        return fragment
