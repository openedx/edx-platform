#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit tests for the Fragment class.
"""

from __future__ import absolute_import, unicode_literals

import ddt
import pytest

from django.test import TestCase

from web_fragments.fragment import Fragment, FragmentResource
from web_fragments.test_utils import (
    CSS_EXPECTED_HTML,
    CSS_LINK_EXPECTED_HTML,
    JS_EXPECTED_HTML,
    JS_LINK_EXPECTED_HTML,
    TEST_CSS,
    TEST_CSS_URL,
    TEST_HTML,
    TEST_JS,
    TEST_JS_INIT_FN,
    TEST_JS_URL,
    TEST_JSON_INIT_ARGS
)

EXPECTED_JS_INIT_VERSION = 1

EXPECTED_RESOURCES = [
    {
        'kind': 'text',
        'data': TEST_CSS,
        'mimetype': 'text/css',
        'placement': 'head',
    },
    {
        'kind': 'url',
        'data': TEST_CSS_URL,
        'mimetype': 'text/css',
        'placement': 'head',
    },
    {
        'kind': 'text',
        'data': TEST_JS,
        'mimetype': 'application/javascript',
        'placement': 'foot',
    },
    {
        'kind': 'url',
        'data': TEST_JS_URL,
        'mimetype': 'application/javascript',
        'placement': 'foot',
    },
]

@ddt.ddt
class TestFragment(TestCase):
    """
    Unit tests for fragments.
    """

    def setUp(self):
        super(TestFragment, self).setUp()

    def create_test_fragment(self):
        """
        Creates a fragment for use in unit tests.
        """
        fragment = Fragment()
        fragment.add_content(TEST_HTML)
        fragment.add_css(TEST_CSS)
        fragment.add_css_url(TEST_CSS_URL)
        fragment.add_javascript(TEST_JS)
        fragment.add_javascript_url(TEST_JS_URL)
        fragment.initialize_js(TEST_JS_INIT_FN, json_args=TEST_JSON_INIT_ARGS)
        return fragment

    def validate_fragment(self, fragment=None, fragment_dict=None):
        """
        Validates that the fields of a fragment are all correct.
        """
        fragment_dict = fragment_dict if fragment_dict else fragment.to_dict()
        assert fragment_dict['content'] == TEST_HTML
        assert fragment_dict['js_init_fn'] == TEST_JS_INIT_FN
        assert fragment_dict['js_init_version'] == EXPECTED_JS_INIT_VERSION
        assert fragment_dict['json_init_args'] == TEST_JSON_INIT_ARGS
        assert fragment_dict['resources'] == EXPECTED_RESOURCES

    def test_to_dict(self):
        """
        Tests the to_dict method.
        """
        fragment = self.create_test_fragment()
        fragment_dict = fragment.to_dict()
        self.validate_fragment(fragment_dict=fragment_dict)

    def test_from_dict(self):
        """
        Tests the from_dict method.
        """
        test_dict = {
            'content': TEST_HTML,
            'resources': EXPECTED_RESOURCES,
            'js_init_fn': TEST_JS_INIT_FN,
            'js_init_version': EXPECTED_JS_INIT_VERSION,
            'json_init_args': TEST_JSON_INIT_ARGS,
        }
        fragment = Fragment.from_dict(test_dict)
        self.validate_fragment(fragment)

    def test_body_html(self):
        """
        Tests the body_html method.
        """
        fragment = self.create_test_fragment()
        html = fragment.body_html()
        assert html == TEST_HTML

    def test_head_html(self):
        """
        Tests the head_html method.
        """
        fragment = self.create_test_fragment()
        html = fragment.head_html().replace('\n', '')
        assert CSS_EXPECTED_HTML.format(css=TEST_CSS) in html
        assert CSS_LINK_EXPECTED_HTML.format(css_url=TEST_CSS_URL) in html

    def test_foot_html(self):
        """
        Tests the foot_html method.
        """
        fragment = self.create_test_fragment()
        html = fragment.foot_html().replace('\n', '')
        assert JS_EXPECTED_HTML.format(js=TEST_JS) in html
        assert JS_LINK_EXPECTED_HTML.format(js_url=TEST_JS_URL) in html

    def test_add_resource(self):
        """
        Tests the add_resource method.
        """
        fragment = Fragment()
        fragment.add_resource(TEST_CSS, 'text/css')
        fragment.add_resource(TEST_JS, 'application/javascript')
        fragment.add_resource(TEST_JS, 'application/javascript', placement='bottom')
        assert fragment.to_dict()['resources'] == [
            {
                'kind': 'text',
                'data': TEST_CSS,
                'mimetype': 'text/css',
                'placement': 'head',
            },
            {
                'kind': 'text',
                'data': TEST_JS,
                'mimetype': 'application/javascript',
                'placement': 'foot',
            },
            {
                'kind': 'text',
                'data': TEST_JS,
                'mimetype': 'application/javascript',
                'placement': 'bottom',
            },
        ]

    def test_add_resource_url(self):
        """
        Tests the add_resource_url method.
        """
        fragment = Fragment()
        fragment.add_resource_url(TEST_CSS_URL, 'text/css')
        fragment.add_resource_url(TEST_JS_URL, 'application/javascript')
        fragment.add_resource_url(TEST_JS_URL, 'application/javascript', placement='bottom')
        assert fragment.to_dict()['resources'] == [
            {
                'kind': 'url',
                'data': TEST_CSS_URL,
                'mimetype': 'text/css',
                'placement': 'head',
            },
            {
                'kind': 'url',
                'data': TEST_JS_URL,
                'mimetype': 'application/javascript',
                'placement': 'foot',
            },
            {
                'kind': 'url',
                'data': TEST_JS_URL,
                'mimetype': 'application/javascript',
                'placement': 'bottom',
            },
        ]

    def test_add_resources(self):
        """
        Tests the add_resources method.
        """
        source_fragment = self.create_test_fragment()
        test_fragment = Fragment('<p>new fragment</p>')
        test_fragment.add_resources([source_fragment])

    @ddt.data(
        (
            FragmentResource('text', TEST_HTML, 'text/html', 'body'),
            TEST_HTML
        ),
        (
            FragmentResource('text', TEST_CSS, 'text/css', 'head'),
            CSS_EXPECTED_HTML.format(css=TEST_CSS)),
        (
            FragmentResource('url', TEST_CSS_URL, 'text/css', 'head'),
            CSS_LINK_EXPECTED_HTML.format(css_url=TEST_CSS_URL)
        ),
        (
            FragmentResource('text', TEST_JS, 'application/javascript', 'body'),
            JS_EXPECTED_HTML.format(js=TEST_JS)),
        (
            FragmentResource('url', TEST_JS_URL, 'application/javascript', 'foot'),
            JS_LINK_EXPECTED_HTML.format(js_url=TEST_JS_URL)
        ),
    )
    @ddt.unpack
    def test_resource_to_html(self, resource, expected_html):
        """
        Tests the resource_to_html method.
        """
        actual_html = Fragment.resource_to_html(resource).replace('\n', '')
        assert actual_html == expected_html

    @ddt.data(
        FragmentResource('unknown', TEST_HTML, 'text/html', 'body'),
        FragmentResource('text', TEST_HTML, 'text/unknown', 'body'),
        FragmentResource('unknown', TEST_CSS, 'text/css', 'head'),
        FragmentResource('unknown', TEST_JS, 'application/javascript', 'body'),
        FragmentResource('text', TEST_HTML, 'unknown', 'body'),
    )
    def test_resource_to_html_exception(self, resource):
        """
        Tests the resource_to_html method.
        """
        with pytest.raises(Exception):
            Fragment.resource_to_html(resource)

    def test_initialize_js(self):
        """
        Tests for initialize_js method.
        """
        fragment = Fragment()
        fragment.initialize_js(TEST_JS_INIT_FN)
        fragment_dict = fragment.to_dict()
        assert fragment_dict['js_init_fn'] == TEST_JS_INIT_FN
        assert fragment_dict['js_init_version'] == EXPECTED_JS_INIT_VERSION
        assert fragment_dict['json_init_args'] is None
