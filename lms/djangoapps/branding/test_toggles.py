"""
Tests for toggles, where there is logic beyond enable/disable.
"""

from unittest.mock import patch
import ddt
from django.test import TestCase
from edx_toggles.toggles.testutils import override_waffle_flag

from lms.djangoapps.branding.toggles import (
    ENABLE_NEW_COURSE_ABOUT_PAGE,
    ENABLE_NEW_INDEX_PAGE,
    use_new_catalog_page,
    use_new_course_about_page,
    use_new_index_page,
)


@ddt.ddt
class TestBrandingToggles(TestCase):
    """
    Tests for toggles, where there is logic beyond enable/disable.
    """

    @ddt.data(True, False)
    @patch("lms.djangoapps.branding.toggles.ENABLE_NEW_CATALOG_PAGE")
    def test_use_new_catalog_page_enabled(
        self, is_waffle_enabled, mock_enable_new_catalog_page
    ):
        # Given legacy catalog feature is / not enabled
        mock_enable_new_catalog_page.is_enabled.return_value = is_waffle_enabled

        # When I check if the feature is enabled
        should_use_new_catalog_page = use_new_catalog_page()

        # Then I respects waffle setting.
        self.assertEqual(should_use_new_catalog_page, is_waffle_enabled)

    @override_waffle_flag(ENABLE_NEW_COURSE_ABOUT_PAGE, True)
    def test_use_new_course_about_page_enabled(self):
        # When I check if the feature is enabled
        should_use_new_course_about_page = use_new_course_about_page()

        # Then I respects waffle setting.
        self.assertEqual(should_use_new_course_about_page, True)

    @override_waffle_flag(ENABLE_NEW_COURSE_ABOUT_PAGE, False)
    def test_use_new_course_about_page_disabled(self):
        # When I check if the feature is enabled
        should_use_new_course_about_page = use_new_course_about_page()

        # Then I respects waffle setting.
        self.assertEqual(should_use_new_course_about_page, False)

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
