"""Tests for the lms module itself."""

from __future__ import absolute_import

import logging
import mimetypes

from django.conf import settings
from django.test import TestCase

from edxmako import LOOKUP, add_lookup
from microsite_configuration import microsite

log = logging.getLogger(__name__)


class LmsModuleTests(TestCase):
    """
    Tests for lms module itself.
    """

    def test_new_mimetypes(self):
        extensions = ['eot', 'otf', 'ttf', 'woff']
        for extension in extensions:
            mimetype, _ = mimetypes.guess_type('test.' + extension)
            self.assertIsNotNone(mimetype)

    def test_api_docs(self):
        """
        Tests that requests to the `/api-docs/` endpoint do not raise an exception.
        """
        assert settings.FEATURES['ENABLE_API_DOCS']
        response = self.client.get('/api-docs/')
        self.assertEqual(200, response.status_code)


class TemplateLookupTests(TestCase):
    """
    Tests for TemplateLookup.
    """

    def test_add_lookup_to_main(self):
        """Test that any template directories added are not cleared when microsites are enabled."""

        add_lookup('main', 'external_module', __name__)
        directories = LOOKUP['main'].directories
        self.assertEqual(len([directory for directory in directories if 'external_module' in directory]), 1)

        # This should not clear the directories list
        microsite.enable_microsites(log)
        directories = LOOKUP['main'].directories
        self.assertEqual(len([directory for directory in directories if 'external_module' in directory]), 1)
