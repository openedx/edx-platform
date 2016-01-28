# -*- coding: utf-8 -*-
"""
Tests microsite_configuration templatetags and helper functions.
"""
from django.test import TestCase
from django.conf import settings
from microsite_configuration.templatetags import microsite as microsite_tags
from microsite_configuration import microsite
from microsite_configuration.backends.base import BaseMicrositeBackend
from microsite_configuration.backends.database import DatabaseMicrositeBackend


class MicrositeTests(TestCase):
    """
    Make sure some of the helper functions work
    """
    def test_breadcrumbs(self):
        crumbs = ['my', 'less specific', 'Page']
        expected = u'my | less specific | Page | edX'
        title = microsite_tags.page_title_breadcrumbs(*crumbs)
        self.assertEqual(expected, title)

    def test_unicode_title(self):
        crumbs = [u'øo', u'π tastes gréât', u'驴']
        expected = u'øo | π tastes gréât | 驴 | edX'
        title = microsite_tags.page_title_breadcrumbs(*crumbs)
        self.assertEqual(expected, title)

    def test_platform_name(self):
        pname = microsite_tags.platform_name()
        self.assertEqual(pname, settings.PLATFORM_NAME)

    def test_breadcrumb_tag(self):
        crumbs = ['my', 'less specific', 'Page']
        expected = u'my | less specific | Page | edX'
        title = microsite_tags.page_title_breadcrumbs_tag(None, *crumbs)
        self.assertEqual(expected, title)

    def test_microsite_template_path(self):
        """
        When an unexistent path is passed to the filter, it should return the same path
        """
        path = microsite_tags.microsite_template_path('footer.html')
        self.assertEqual("footer.html", path)

    def test_get_backend_raise_error_for_invalid_class(self):
        """
        Test get_backend returns None for invalid paths
        and raises TypeError when invalid class or class name is a method.
        """
        # invalid backend path
        self.assertEqual(microsite.get_backend(None, BaseMicrositeBackend), None)

        # invalid class or class name is a method
        with self.assertRaises(TypeError):
            microsite.get_backend('microsite_configuration.microsite.get_backend', BaseMicrositeBackend)

    def test_get_backend_raise_error_when_module_has_no_class(self):
        """
        Test get_backend raises ValueError when module does not have a class.
        """
        # module does not have a class
        with self.assertRaises(ValueError):
            microsite.get_backend('microsite_configuration.microsite.invalid_method', BaseMicrositeBackend)

    def test_get_backend_for_valid_class(self):
        """
        Test get_backend loads class if class exists.
        """
        # load a valid class
        self.assertIsInstance(
            microsite.get_backend(
                'microsite_configuration.backends.database.DatabaseMicrositeBackend', BaseMicrositeBackend
            ),
            DatabaseMicrositeBackend
        )
