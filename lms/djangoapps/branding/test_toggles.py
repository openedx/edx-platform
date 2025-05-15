"""
Tests for toggles, where there is logic beyond enable/disable.
"""

import ddt
from django.test import TestCase
from edx_toggles.toggles.testutils import override_waffle_flag

from lms.djangoapps.branding.toggles import (
    ENABLE_NEW_INDEX_PAGE,
    use_new_index_page,
)


@ddt.ddt
class TestBrandingToggles(TestCase):
    """
    Tests for toggles, where there is logic beyond enable/disable.
    """

    @override_waffle_flag(ENABLE_NEW_INDEX_PAGE, True)
    def test_use_new_index_page_enabled(self):
        # When I check if the feature is enabled
        should_use_new_index_page = use_new_index_page()

        # Then I respects waffle setting.
        self.assertEqual(should_use_new_index_page, True)

    @override_waffle_flag(ENABLE_NEW_INDEX_PAGE, False)
    def test_use_new_index_page_disabled(self):
        # When I check if the feature is enabled
        should_use_new_index_page = use_new_index_page()

        # Then I respects waffle setting.
        self.assertEqual(should_use_new_index_page, False)
