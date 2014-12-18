"""
Acceptance tests for Studio related to the asset index page.
"""
import unittest
from bok_choy.web_app_test import WebAppTest
import bok_choy.browser
from ...pages.studio.asset_index import AssetIndexPage

from base_studio_test import StudioCourseTest


class AssetIndexTest(StudioCourseTest):

    """
    Tests for the Asset index page.
    """

    def setUp(self):
        super(AssetIndexTest, self).setUp()
        self.asset_page = AssetIndexPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """
        Populate the children of the test course fixture.
        """
        self.course_fixture.add_asset(['image.jpg', 'textbook.pdf'])

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self.asset_page.visit()

    def test_type_filter_exists(self):
        """
        Make sure type filter is on the page.
        """
        browser = bok_choy.browser.browser()
        self.addCleanup(browser.quit)
        assert self.asset_page.visit().type_filter_on_page() == True

    def test_filter_results(self):
        """
        Make sure type filter actually filters the results.
        """
        all_results = len(self.asset_page.visit().return_results_set())
        if self.asset_page.select_type_filter(1):
            filtered_results = len(self.asset_page.return_results_set())
            assert self.asset_page.type_filter_header_label_visible()
            assert all_results > filtered_results
        else:
            msg = "Could not open select Type filter"
            raise StudioApiLoginError(msg)
