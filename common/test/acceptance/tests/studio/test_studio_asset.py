"""
Acceptance tests for Studio related to the asset index page.
"""
import os

from common.test.acceptance.pages.studio.asset_index import AssetIndexPageStudioFrontend
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.pages.studio.asset_index import UPLOAD_FILE_DIR


class AssetIndexTestStudioFrontend(StudioCourseTest):
    """Tests for the Asset index page."""
    shard = 21

    def setUp(self, is_staff=False):  # pylint: disable=arguments-differ
        super(AssetIndexTestStudioFrontend, self).setUp()
        self.asset_page = AssetIndexPageStudioFrontend(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """Populate the children of the test course fixture."""
        self.course_fixture.add_asset(['image.jpg', 'textbook.pdf'])

    def test_page_with_assets_elements_load(self):
        """Make sure all elements are on page for a course with assets."""
        self.asset_page.visit()
        assert self.assert_studio_frontend_container_exists()
        assert self.assert_table_exists()
        assert self.assert_type_filter_exists()
        assert self.assert_upload_element_exists()
        assert self.assert_sortable_table_heading_elements_exist()
        assert self.assert_status_element_exists()
        assert self.assert_pagination_element_exists()
        assert self.assert_search_element_exists()

    def assert_page_without_filter_results_elements_load(self):
        """Make sure correct elements are on page for a filter with no results."""
        assert self.assert_studio_frontend_container_exists()
        assert not self.assert_table_exists()
        assert not self.assert_sortable_table_heading_elements_exist()
        assert not self.assert_pagination_element_exists()

        assert self.assert_search_element_exists()
        assert self.assert_status_element_exists()
        assert self.assert_type_filter_exists()
        assert self.assert_upload_element_exists()
        assert self.assert_no_results_headings_exist()
        assert self.assert_clear_filters_button_exists()

    def assert_studio_frontend_container_exists(self):
        return self.asset_page.is_studio_frontend_container_on_page()

    def assert_table_exists(self):
        """Make sure table is on the page."""
        return self.asset_page.is_table_element_on_page()

    def assert_type_filter_exists(self):
        """Make sure type filter is on the page."""
        return self.asset_page.is_filter_element_on_page() is True

    def assert_upload_element_exists(self):
        """Make sure upload dropzone is on the page."""
        return self.asset_page.is_upload_element_on_page()

    def assert_sortable_table_heading_elements_exist(self):
        """
        Make sure the sortable table buttons are on the page and there arethree of them."""
        return self.asset_page.number_of_sortable_buttons_in_table_heading == 3

    def assert_status_element_exists(self):
        """Make sure status alert is on the page but not visible."""
        return self.asset_page.is_status_alert_element_on_page()

    def assert_pagination_element_exists(self):
        """Make sure pagination element is on the page."""
        return self.asset_page.is_pagination_element_on_page() is True

    def assert_search_element_exists(self):
        """Make sure search element is on the page."""
        return self.asset_page.is_search_element_on_page() is True

    def assert_no_results_headings_exist(self):
        """Make sure headings with text for no results is on the page."""
        return self.asset_page.are_no_results_headings_on_page()

    def assert_clear_filters_button_exists(self):
        """Make sure the clear filters button is on the page."""
        return self.asset_page.is_no_results_clear_filter_button_on_page()

    def test_clicking_filter_with_results(self):
        """Make sure clicking the Images filter that has results and performs the filtering correctly."""
        self.asset_page.visit()
        all_results = self.asset_page.number_of_asset_files
        # select Images
        assert self.asset_page.select_type_filter(3)
        filtered_results = self.asset_page.number_of_asset_files
        assert all_results > filtered_results
        assets_file_types = self.asset_page.asset_files_types
        for file_type in assets_file_types:
            assert 'image' in file_type

    def test_clicking_filter_without_results(self):
        """
        Make sure clicking a type filter that has no results performs the filtering correctly, updates the page view to
        display the no results view, and displays the correct elements.
        """
        self.asset_page.visit()
        all_results = self.asset_page.number_of_asset_files
        # select Audio
        assert self.asset_page.select_type_filter(0)
        filtered_results = self.asset_page.number_of_asset_files
        assert all_results > filtered_results
        assert filtered_results == 0
        self.assert_page_without_filter_results_elements_load()

    def test_clicking_clear_filter(self):
        """Make sure clicking the 'Clear filter' button clears the checkbox and returns results."""
        self.asset_page.visit()
        all_results = self.asset_page.number_of_asset_files
        # select Audio
        assert self.asset_page.select_type_filter(0)
        assert self.asset_page.click_clear_filters_button()
        new_results = self.asset_page.number_of_asset_files
        assert new_results == all_results
        self.test_page_with_assets_elements_load()

    def test_lock(self):
        """Make sure clicking the lock button toggles correctly."""
        self.asset_page.visit()
        # Verify that a file can be locked
        self.asset_page.set_asset_lock()
        # Get the list of locked assets, there should be one
        locked_assets = self.asset_page.asset_lock_buttons(locked_only=True)
        self.assertEqual(len(locked_assets), 1)

        # Confirm that there are 2 assets, with the first
        # locked and the second unlocked.
        all_assets = self.asset_page.asset_lock_buttons(locked_only=False)
        self.assertEqual(len(all_assets), 2)
        self.assertTrue('fa-lock' in all_assets[0].get_attribute('class'))
        self.assertTrue('fa-unlock' in all_assets[1].get_attribute('class'))

    def test_delete_and_upload(self):
        """
        Upload specific files to page.
        Start by deleting all files, to ensure starting on a blank slate.
        """
        self.asset_page.visit()
        self.asset_page.delete_all_assets()
        file_names = [u'file-0.png', u'file-13.pdf', u'file-26.js', u'file-39.txt']
        # Upload the files
        self.asset_page.upload_new_files(file_names)
        # Assert that the files have been uploaded.
        all_assets = self.asset_page.number_of_asset_files
        self.assertEqual(all_assets, 4)
        self.assertEqual(file_names.sort(), self.asset_page.asset_files_names.sort())

    def test_display_name_sort(self):
        """Make sure clicking the display name sort button sorts the files."""
        self.asset_page.visit()
        # the default sort is on 'Date Added', so sort on 'Name' to start
        # with a fresh state
        self.asset_page.click_sort_button('Name')
        before_sort_file_names = self.asset_page.asset_files_names
        sorted_file_names = sorted(before_sort_file_names)

        assert self.asset_page.click_sort_button('Name')
        after_sort_file_names = self.asset_page.asset_files_names
        assert before_sort_file_names != after_sort_file_names
        assert sorted_file_names == after_sort_file_names

        assert self.asset_page.click_sort_button('Name')
        assert self.asset_page.asset_files_names == before_sort_file_names


class AssetIndexTestStudioFrontendPagination(StudioCourseTest):
    """Pagination tests for the Asset index page."""

    def setUp(self, is_staff=False):  # pylint: disable=arguments-differ
        super(AssetIndexTestStudioFrontendPagination, self).setUp()
        self.asset_page = AssetIndexPageStudioFrontend(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """Populate the children of the test course fixture and upload 49 files."""
        files = []

        for file_name in os.listdir(UPLOAD_FILE_DIR):
            file_path = 'studio-uploads/' + file_name
            files.append(file_path)
        course_fixture.add_asset(files)

    def assert_correct_number_of_buttons(self, count):
        """Make sure the correct number of buttons are on the page; includes previous and next. """
        assert self.asset_page.number_of_pagination_buttons == count

    def assert_correct_direction_buttons(self):
        """Make sure the previous and next pagination buttons are on the page."""
        assert self.asset_page.is_previous_button_on_page
        assert self.asset_page.is_next_button_on_page

    def test_pagination_exists(self):
        """Make sure the pagination elements are on the page."""
        self.asset_page.visit()
        self.assert_correct_number_of_buttons(4)
        self.assert_correct_direction_buttons()

    def test_pagination_page_click(self):
        """Make clicking the second page button displays the second page of files."""
        self.asset_page.visit()

        first_page_file_names = self.asset_page.asset_files_names
        assert self.asset_page.click_pagination_page_button(2)
        assert self.asset_page.is_selected_page(2)
        assert self.asset_page.number_of_asset_files == 1
        second_page_file_names = self.asset_page.asset_files_names

        assert first_page_file_names != second_page_file_names

    def test_pagination_next_and_previous_click(self):
        """
        Make sure clicking the next button displays the next page of files and
        clicking the previous button displays the previous page of files.
        """
        self.asset_page.visit()

        first_page_file_names = self.asset_page.asset_files_names
        assert self.asset_page.click_pagination_next_button()
        assert self.asset_page.is_selected_page(2)
        assert self.asset_page.number_of_asset_files == 1
        next_page_file_names = self.asset_page.asset_files_names

        assert first_page_file_names != next_page_file_names

        assert self.asset_page.click_pagination_previous_button()
        assert self.asset_page.is_selected_page(1)
        assert self.asset_page.number_of_asset_files == 50
        previous_page_file_names = self.asset_page.asset_files_names

        assert first_page_file_names == previous_page_file_names
