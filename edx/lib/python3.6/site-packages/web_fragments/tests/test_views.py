#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit tests for web fragment views
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json

import ddt
import pytest

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory

from web_fragments.examples.views import EXAMPLE_FRAGMENT_VIEW_NAME, ExampleFragmentView
from web_fragments.test_utils import TEST_HTML
from web_fragments.views import FragmentView


@ddt.ddt
class TestViews(TestCase):
    """
    Unit tests for web fragment views.
    """

    def setUp(self):
        super(TestViews, self).setUp()
        self.requests_factory = RequestFactory()

    def create_mock_request(self, method=None, arguments=None, http_accept='text/html'):
        """
        Creates a mock request to the test fragment view.
        """
        url = reverse(EXAMPLE_FRAGMENT_VIEW_NAME) + ('/?' + arguments if arguments else '')
        method = method if method else self.requests_factory.get
        return method(url, HTTP_ACCEPT=http_accept)

    def invoke_test_view(self, method=None, arguments=None, http_accept='text/html', expected_status_code=200):
        """
        Invokes the test view with the specified arguments (if provided).
        """
        request = self.create_mock_request(method=method, arguments=arguments, http_accept=http_accept)
        response = ExampleFragmentView.as_view()(request)
        assert response.status_code == expected_status_code
        return response

    @ddt.data(
        ('format=json', 'text/html'),
        (None, 'application/web-fragment'),
    )
    @ddt.unpack
    def test_get_json(self, arguments, http_accept):
        """
        Test that the view returns the correct JSON when requested.
        """
        response = self.invoke_test_view(arguments=arguments, http_accept=http_accept)
        fragment_json = json.loads(response.content.decode(response.charset))
        assert fragment_json['content'] == TEST_HTML

    @ddt.data(
        ('format=html', 'text/html'),
        (None, 'text/html'),
    )
    @ddt.unpack
    def test_get_html(self, arguments, http_accept):
        """
        Test fragment getter when html is requested
        """
        response = self.invoke_test_view(arguments=arguments, http_accept=http_accept)
        assert TEST_HTML in response.content.decode(response.charset)

    def test_render_fragment_error(self):
        """
        Verifies that render_fragment throws an unimplemented error on the base class.
        """
        class MockFragmentView(FragmentView):
            """
            Mock fragment view to verify the default render_fragment method
            """
            def render_to_fragment(self, request, **kwargs):
                super(MockFragmentView, self).render_to_fragment(request, **kwargs)

        view = MockFragmentView()
        request = self.create_mock_request()
        with pytest.raises(NotImplementedError):
            view.render_to_fragment(request)

    def test_render_with_no_fragment(self):
        """
        Verifies that a fragment view can render with no fragment.
        """
        request = self.create_mock_request()
        response = ExampleFragmentView().render_standalone_response(request, None)
        assert response.status_code == 204
