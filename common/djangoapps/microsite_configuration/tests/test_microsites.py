# -*- coding: utf-8 -*-
"""
Tests microsite_configuration templatetags and helper functions.
"""
from mock import patch
from django.test import TestCase
from django.conf import settings
from microsite_configuration.templatetags import microsite


class MicroSiteTests(TestCase):
    """
    Make sure some of the helper functions work
    """
    def test_breadcrumbs(self):
        crumbs = ['my', 'less specific', 'Page']
        expected = u'my | less specific | Page | edX'
        title = microsite.page_title_breadcrumbs(*crumbs)
        self.assertEqual(expected, title)

    def test_unicode_title(self):
        crumbs = [u'øo', u'π tastes gréât', u'驴']
        expected = u'øo | π tastes gréât | 驴 | edX'
        title = microsite.page_title_breadcrumbs(*crumbs)
        self.assertEqual(expected, title)

    def test_platform_name(self):
        pname = microsite.platform_name()
        self.assertEqual(pname, settings.PLATFORM_NAME)

    def test_breadcrumb_tag(self):
        crumbs = ['my', 'less specific', 'Page']
        expected = u'my | less specific | Page | edX'
        title = microsite.page_title_breadcrumbs_tag(None, *crumbs)
        self.assertEqual(expected, title)

    def test_microsite_template_path(self):
        relative_path = 'some_template.html'
        resolved_path = 'resolved/path/to/some_template.html'
        with patch(
            'microsite_configuration.microsite.get_template_path',
            return_value=resolved_path
        ) as mock:
            result = microsite.microsite_template_path(relative_path)
            mock.assert_called_once_with(relative_path)
            self.assertEqual(result, resolved_path)
