"""
Tests for Units internal api.
"""
from django.test import TestCase

from opaque_keys.edx.locator import LibraryLocatorV2, LibraryContainerLocator

from .. import api

class UnitLibraryTest(TestCase):

    library_key_str = 'lib:foobar_content:foobar_library'

    def test_get_library_unit_usage_key(self):
        """
        Test build the unit usage key
        """
        library_key = LibraryLocatorV2.from_string(self.library_key_str)
        unit_id = 'test-unit'
        expected_key = f'lct:{library_key.org}:{library_key.slug}:unit:{unit_id}'

        unit_key = api.get_library_unit_usage_key(library_key, unit_id)

        assert unit_key.library_key == library_key
        assert unit_key.container_id == unit_id
        assert str(unit_key) == expected_key
