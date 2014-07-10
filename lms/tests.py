"""Tests for the lms module itself."""

import mimetypes

from django.test import TestCase

from edxmako import add_lookup, LOOKUP
from lms import startup


class LmsModuleTests(TestCase):
    """
    Tests for lms module itself.
    """

    def test_new_mimetypes(self):
        extensions = ['eot', 'otf', 'ttf', 'woff']
        for extension in extensions:
            mimetype, _ = mimetypes.guess_type('test.' + extension)
            self.assertIsNotNone(mimetype)


class TemplateLookupTests(TestCase):
    """
    Tests for TemplateLookup.
    """

    def test_add_lookup_to_main(self):
        """Test that any template directories added are not cleared when microsites are enabled."""

        add_lookup('main', 'external_module', __name__)
        directories = LOOKUP['main'].directories
        self.assertEqual(len([dir for dir in directories if 'external_module' in dir]), 1)

        # This should not clear the directories list
        startup.enable_microsites()
        directories = LOOKUP['main'].directories
        self.assertEqual(len([dir for dir in directories if 'external_module' in dir]), 1)
