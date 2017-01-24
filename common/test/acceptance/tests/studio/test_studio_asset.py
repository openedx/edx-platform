"""
Acceptance tests for Studio related to the asset index page.
"""

from flaky import flaky
from unittest import skip

from common.test.acceptance.pages.studio.asset_index import AssetIndexPage

from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.fixtures.base import StudioApiLoginError
from common.test.acceptance.tests.helpers import skip_if_browser


@skip('FEDX-88')
class AssetIndexTest(StudioCourseTest):

    """
    Tests for the Asset index page.
    """
    def setUp(self, is_staff=False):
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

    @skip_if_browser('chrome')  # TODO Need to fix test_page_existance for this for chrome browser
    @flaky      # TODO fix this FEDX-88
    def test_type_filter_exists(self):
        """
        Make sure type filter is on the page.
        """
        self.asset_page.visit()
        assert self.asset_page.type_filter_on_page() is True

    @skip_if_browser('chrome')  # TODO Need to fix test_page_existance for this for chrome browser
    @flaky    # TODO FEDX-88
    def test_filter_results(self):
        """
        Make sure type filter actually filters the results.
        """
        self.asset_page.visit()
        all_results = len(self.asset_page.return_results_set())
        if self.asset_page.select_type_filter(1):
            filtered_results = len(self.asset_page.return_results_set())
            assert self.asset_page.type_filter_header_label_visible()
            assert all_results > filtered_results
        else:
            msg = "Could not open select Type filter"
            raise StudioApiLoginError(msg)
