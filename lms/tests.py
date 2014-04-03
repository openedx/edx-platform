"""Tests for the lms module itself."""

from django.test import TestCase

from edxmako import add_lookup, LOOKUP
from lms import startup

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
