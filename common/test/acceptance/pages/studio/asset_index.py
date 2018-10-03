"""
The Files and Uploads page for a course in Studio
"""

import os
import urllib
from path import Path

from bok_choy.javascript import wait_for_js
from bok_choy.promise import EmptyPromise
from opaque_keys.edx.locator import CourseLocator
from common.test.acceptance.pages.common.utils import sync_on_notification
from common.test.acceptance.pages.studio import BASE_URL
from common.test.acceptance.pages.studio.course_page import CoursePage

# file path found from CourseFixture logic
UPLOAD_SUFFIX = '/data/uploads/studio-uploads/'
UPLOAD_FILE_DIR = Path(__file__).abspath().dirname().dirname().dirname().dirname() + UPLOAD_SUFFIX  # pylint: disable=no-value-for-parameter


class AssetIndexPageStudioFrontend(CoursePage):
    """The Files and Uploads page for a course in Studio"""

    PAGINATION_PAGE_ELEMENT = ".pagination .page-item"
    TABLE_SORT_BUTTONS = 'th.sortable button.btn-header'
    TYPE_FILTER_ELEMENT = 'div[data-identifier="asset-filters"] .form-group'
    URL_PATH = "assets"

    @property
    def url(self):
        """Construct a URL to the page within the course."""
        # TODO - is there a better way to make this agnostic to the underlying default module store?
        default_store = os.environ.get('DEFAULT_STORE', 'draft')
        course_key = CourseLocator(
            self.course_info['course_org'],
            self.course_info['course_num'],
            self.course_info['course_run'],
            deprecated=(default_store == 'draft')
        )
        url = "/".join([BASE_URL, self.URL_PATH, urllib.quote_plus(unicode(course_key))])
        return url if url[-1] == '/' else url + '/'

    @wait_for_js
    def is_browser_on_page(self):
        return all([
            self.q(css='body.view-uploads').present,
            self.q(css='.page-header').present,
            self.q(css='#root').present,
            not self.q(css='div.ui-loading').visible,
        ])

    @wait_for_js
    def is_studio_frontend_container_on_page(self):
        """Checks that the studio-frontend container has been loaded."""
        return self.q(css='.SFE').present

    @wait_for_js
    def is_table_element_on_page(self):
        """Checks that table is on the page."""
        return self.q(css='table.table-responsive').present

    @wait_for_js
    def is_upload_element_on_page(self):
        """Checks that the dropzone area is on the page."""
        return self.q(css='.drop-zone').present

    @wait_for_js
    def is_filter_element_on_page(self):
        """Checks that type filter heading and checkboxes are on the page."""
        return all([
            self.q(css='.filter-heading').is_present,
            self.q(css=self.TYPE_FILTER_ELEMENT).present,
        ])

    @wait_for_js
    def is_pagination_element_on_page(self):
        """Checks that pagination is on the page."""
        return self.q(css='.pagination').present

    @wait_for_js
    def is_search_element_on_page(self):
        """Checks that search bar is on the page."""
        return self.q(css="[name='search']").present

    @wait_for_js
    def is_status_alert_element_on_page(self):
        """Checks that status alert is hidden on page."""
        return all([
            self.q(css='.alert').present,
            not self.q(css='.alert').visible,
        ])

    @wait_for_js
    def are_no_results_headings_on_page(self):
        """Checks that no results page text is on page."""
        return self.q(css='.SFE-wrapper h3').filter(lambda el: el.text == '0 files found').present

    @wait_for_js
    def is_no_results_clear_filter_button_on_page(self):
        """Checks that no results clear filter button is on page."""
        return self.q(css='.SFE-wrapper button.btn').filter(
            lambda el: el.text == 'Clear all filters'
        ).present

    @property
    @wait_for_js
    def asset_files_names(self):
        """
        Get the names of uploaded files.
        Returns:
            list: Names of files on current page.
        """
        return self.q(css='span[data-identifier="asset-file-name"]').text

    @property
    @wait_for_js
    def asset_files_types(self):
        """
        Get the file types of uploaded files.
        Returns:
            list: File types of files on current page.
        """
        return self.q(css='span[data-identifier="asset-content-type"]').text

    @property
    @wait_for_js
    def number_of_asset_files(self):
        """
        Returns the number of files on the current page.
        """
        return len(self.q(css='span[data-identifier="asset-file-name"]').execute())

    @property
    @wait_for_js
    def number_of_filters(self):
        return len(self.q(css='.form-check').execute())

    @property
    @wait_for_js
    def number_of_sortable_buttons_in_table_heading(self):
        return len(self.q(css=self.TABLE_SORT_BUTTONS).execute())

    @property
    @wait_for_js
    def asset_delete_buttons(self):
        """Return a list of WebElements for deleting the assets"""
        css = 'button[data-identifier="asset-delete-button"]'
        return self.q(css=css).execute()

    @wait_for_js
    def asset_lock_buttons(self, locked_only=True):
        """
        Return a list of WebElements of the lock buttons for assets
        or an empty list if there are none.
        """
        css = 'button[data-identifier="asset-lock-button"]'
        if locked_only:
            css = '{}.{}'.format(css, 'fa-lock')
        return self.q(css=css).execute()

    @wait_for_js
    def select_type_filter(self, filter_number):
        """
        Selects Images Type filter checkbox which filters the results.
        Returns False if no filter.
        """
        self.wait_for_ajax()
        if self.is_filter_element_on_page():
            self.q(css=self.TYPE_FILTER_ELEMENT + ' .form-check .form-check-input').nth(filter_number).click()
            self.wait_for_ajax()
            return True
        return False

    @wait_for_js
    def click_clear_filters_button(self):
        """
        Clicks 'Clear all filters' button.
        Returns False if no 'Clear all filters' button.
        """
        self.wait_for_ajax()
        if self.is_no_results_clear_filter_button_on_page():
            self.q(css='.SFE-wrapper button.btn').filter(
                lambda el: el.text == 'Clear all filters'
            ).click()
            self.wait_for_ajax()
            return True
        return False

    @wait_for_js
    def set_asset_lock(self, index=0):
        """
        Set the state of the asset in the row specified by index
         to locked or unlocked by clicking the button.
        Note: this will raise an IndexError if the row does not exist.
        """
        lock_button = self.q(css=".table-responsive tbody tr td:nth-child(7) button").execute()[index]
        lock_button.click()
        # Click initiates an ajax call, waiting for it to complete
        self.wait_for_ajax()
        sync_on_notification(self)

    @wait_for_js
    def confirm_asset_deletion(self):
        """ Click to confirm deletion and sync on the notification."""
        confirmation_title_selector = '.modal'
        self.q(css=confirmation_title_selector + ' button[data-identifier="asset-confirm-delete-button"]').click()
        # Click initiates an ajax call, waiting for it to complete
        self.wait_for_ajax()
        sync_on_notification(self)

    @wait_for_js
    def delete_first_asset(self):
        """ Deletes file then clicks delete on confirmation."""
        self.q(css='.fa-trash').first.click()
        self.confirm_asset_deletion()

    @wait_for_js
    def delete_asset_named(self, name):
        """Delete the asset with the specified name."""
        names = self.asset_files_names
        if name not in names:
            raise LookupError('Asset with filename {} not found.'.format(name))
        delete_buttons = self.asset_delete_buttons
        assets = dict(zip(names, delete_buttons))
        # Now click the link in that row
        assets.get(name).click()
        self.confirm_asset_deletion()

    @wait_for_js
    def delete_all_assets(self):
        """Delete all uploaded assets."""
        while self.number_of_asset_files:
            self.delete_first_asset()

        self.wait_for_ajax()
        self.wait_for_page()

    @wait_for_js
    def upload_new_files(self, file_names):
        """
        Upload file(s).

        Arguments:
            file_names (list): file name(s) we want to upload.
        """
        file_input_css = 'input[type=file]'

        for file_name in file_names:
            # Make file input field visible.
            self.browser.execute_script('$("{}").css("display","block");'.format(file_input_css))
            self.wait_for_element_visibility(file_input_css, "Input is visible")
            #Send file to upload
            self.q(css=file_input_css).results[0].send_keys(
                UPLOAD_FILE_DIR + file_name)
            self.q(css=file_input_css).results[0].clear()
            # Wait for status alert and close
            self.wait_for_element_visibility(
                '.alert', 'Upload status alert is visible.')
            self.q(css='.close').first.click()

        self.wait_for_ajax()
        self.wait_for_files_upload(len(file_names))

    @wait_for_js
    def wait_for_files_upload(self, number):
        """
        Wait for file(s) to upload.

        Arguments:
            number (int): number of uploaded files.
        """
        return EmptyPromise(
            lambda: self.number_of_asset_files == number,
            "Files finished uploading"
        ).fulfill()

    @property
    @wait_for_js
    def is_previous_button_enabled(self):
        return 'disabled' not in self.q(css=self.PAGINATION_PAGE_ELEMENT).first.attrs('class')[0]

    @property
    @wait_for_js
    def is_next_button_enabled(self):
        return 'disabled' not in self.q(css=self.PAGINATION_PAGE_ELEMENT).nth(
            self.number_of_pagination_buttons - 1).attrs('class')[0]

    @property
    @wait_for_js
    def is_previous_button_on_page(self):
        """Note: the two conditions cover when the button is and is not disabled."""
        return 'previous' in self.q(css=self.PAGINATION_PAGE_ELEMENT + ' .previous').text

    @property
    @wait_for_js
    def is_next_button_on_page(self):
        """Note: the two conditions cover when the button is and is not disabled."""
        return 'next' in self.q(css=self.PAGINATION_PAGE_ELEMENT + ' .next').text

    @wait_for_js
    def click_pagination_page_button(self, index):
        """
        Click pagination page button.
        Return False if no pagination page button at specified index.
        """
        self.wait_for_ajax()
        if index <= self.number_of_pagination_buttons:
            self.q(css=self.PAGINATION_PAGE_ELEMENT + ' .page-link').nth(index)[0].click()
            self.wait_for_ajax()
            return True
        return False

    @wait_for_js
    def click_pagination_next_button(self):
        """
        Click pagination next button.
        Return False if next button disabled.
        """
        self.wait_for_ajax()
        if self.is_next_button_enabled:
            self.q(css=self.PAGINATION_PAGE_ELEMENT + ' .next.page-link')[0].click()
            self.wait_for_ajax()
            return True
        return False

    @wait_for_js
    def click_pagination_previous_button(self):
        """
        Click pagination previous button.
        Return False if previous button disabled.
        """
        self.wait_for_ajax()
        if self.is_previous_button_enabled:
            self.q(css=self.PAGINATION_PAGE_ELEMENT + ' .previous.page-link')[0].click()
            self.wait_for_ajax()
            return True
        return False

    @property
    @wait_for_js
    def number_of_pagination_buttons(self):
        """Return the number of total pagination page buttons, including previous, pages, and next buttons."""
        return len(self.q(css=self.PAGINATION_PAGE_ELEMENT + ' .page-link'))

    @wait_for_js
    def is_selected_page(self, index):
        """
        Return true if the pagination page at the current index is selected.
        Return false if the pagination page at the current index does not exist
        or is not selected.

        Note: this *does* include the 'previous' and 'next' buttons
        Note: 0-indexed
        """
        if index < self.number_of_pagination_buttons:
            return 'active' in self.q(css=self.PAGINATION_PAGE_ELEMENT).nth(index)[0].get_attribute('class')
        return False

    @wait_for_js
    def click_sort_button(self, button_text):
        """
        Click sort button with the specified button text.

        Arguments:
            button_text (string): text of the sort button to click.
        """
        self.wait_for_ajax()
        sort_button = self.q(css=self.TABLE_SORT_BUTTONS).filter(
            lambda el: button_text in el.text
        )

        if sort_button:
            sort_button.click()
            return True
        return False
