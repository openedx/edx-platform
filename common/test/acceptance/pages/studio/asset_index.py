"""
The Files and Uploads page for a course in Studio
"""

import os
import urllib

from bok_choy.javascript import wait_for_js
from opaque_keys.edx.locator import CourseLocator

from common.test.acceptance.pages.studio import BASE_URL
from common.test.acceptance.pages.studio.course_page import CoursePage


class AssetIndexPage(CoursePage):

    """
    The Files and Uploads page for a course in Studio
    """

    url_path = "assets"
    type_filter_element = '#js-asset-type-col'

    @property
    def url(self):
        """
        Construct a URL to the page within the course.
        """
        # TODO - is there a better way to make this agnostic to the underlying default module store?
        default_store = os.environ.get('DEFAULT_STORE', 'draft')
        course_key = CourseLocator(
            self.course_info['course_org'],
            self.course_info['course_num'],
            self.course_info['course_run'],
            deprecated=(default_store == 'draft')
        )
        url = "/".join([BASE_URL, self.url_path, urllib.quote_plus(unicode(course_key))])
        return url if url[-1] is '/' else url + '/'

    @wait_for_js
    def is_browser_on_page(self):
        return all([
            self.q(css='body.view-uploads').present,
            self.q(css='.page-header').present,
            not self.q(css='div.ui-loading').visible,
        ])

    @wait_for_js
    def type_filter_on_page(self):
        """
        Checks that type filter is in table header.
        """
        return self.q(css=self.type_filter_element).present

    @wait_for_js
    def type_filter_header_label_visible(self):
        """
        Checks type filter label is added and visible in the pagination header.
        """
        return self.q(css='span.filter-column').visible

    @wait_for_js
    def click_type_filter(self):
        """
        Clicks type filter menu.
        """
        self.q(css=".filterable-column .nav-item").click()

    @wait_for_js
    def select_type_filter(self, filter_number):
        """
        Selects Type filter from dropdown which filters the results.
        Returns False if no filter.
        """
        self.wait_for_ajax()
        if self.q(css=".filterable-column .nav-item").is_present():
            if not self.q(css=self.type_filter_element + " .wrapper-nav-sub").visible:
                self.q(css=".filterable-column > .nav-item").first.click()
            self.wait_for_element_visibility(
                self.type_filter_element + " .wrapper-nav-sub", "Type Filter promise satisfied.")
            self.q(css=self.type_filter_element + " .column-filter-link").nth(filter_number).click()
            self.wait_for_ajax()
            return True
        return False

    def return_results_set(self):
        """
        Returns the asset set from the page
        """
        return self.q(css="#asset-table-body tr").results

class AssetIndexPageStudioFrontend(CoursePage):

    """
    The Files and Uploads page for a course in Studio
    """

    url_path = "assets"

    @property
    def url(self):
        """
        Construct a URL to the page within the course.
        """
        # TODO - is there a better way to make this agnostic to the underlying default module store?
        default_store = os.environ.get('DEFAULT_STORE', 'draft')
        course_key = CourseLocator(
            self.course_info['course_org'],
            self.course_info['course_num'],
            self.course_info['course_run'],
            deprecated=(default_store == 'draft')
        )
        url = "/".join([BASE_URL, self.url_path, urllib.quote_plus(unicode(course_key))])
        return url if url[-1] is '/' else url + '/'

    @wait_for_js
    def is_browser_on_page(self):
        return all([
            self.q(css='body.view-uploads').present,
            self.q(css='.page-header').present,
            self.q(css='#root').present,
            not self.q(css='div.ui-loading').visible,
        ])

    @wait_for_js
    def is_sfe_container_on_page(self):
        """
        Checks that the studio-frontend container has been loaded.
        """
        return self.q(css='.SFE__container').present

    @wait_for_js
    def is_upload_element_on_page(self):
        """
        Checks that the dropzone area is on the page.
        """
        return self.q(css='.AssetsDropZone__drop-zone').present

    #
    # Should we add an id value to the div surrounding the assets filters?
    # self.q(css='div[@role = group]').present
    #
    @wait_for_js
    def filter_element_on_page(self):
        """
        Checks that type filter heading and checkboxes are on the page.
        """
        return all([
            self.q(css='.AssetsFilters__filter-heading').present,
            self.q(css='.CheckBoxGroup__form-group').present,
        ])

    #
    # next two items validate clicking the dropdown and selecting from the dropdown
    #
    # @wait_for_js
    # def click_type_filter(self):
    #     """
    #     Clicks type filter Images checkbox.
    #     """
    #     self.q(css=".asInput__form-check-input #Images").click()

    # @wait_for_js
    # def select_type_filter(self, filter_number):
    #     """
    #     Selects Images Type filter checkbox which filters the results.
    #     Returns False if no filter.
    #     """
    #     self.wait_for_ajax()
    #     if self.q(css=".filterable-column .nav-item").is_present():
    #         if not self.q(css=self.type_filter_element + " .wrapper-nav-sub").visible:
    #             self.q(css=".filterable-column > .nav-item").first.click()
    #         self.wait_for_element_visibility(
    #             self.type_filter_element + " .wrapper-nav-sub", "Type Filter promise satisfied.")
    #         self.q(css=self.type_filter_element + " .column-filter-link").nth(filter_number).click()
    #         self.wait_for_ajax()
    #         return True
    #     return False

    @wait_for_js
    def sortable_element_on_page(self):
        """
        Checks that the table headings are sortable.
        how to check for all 3? should we? 
        """
        return self.q(css='th.sortable').present

    @wait_for_js
    def status_alert_element_on_page(self):
        """
        Checks that status alert is hidden on page.
        """
        return all([
            self.q(css='.StatusAlert__alert').present,
            not self.q(css='StatusAlert__alert').visible,
        ])

    @wait_for_js
    def pagination_element_on_page(self):
        """
        Checks that pagination is on the page.
        """
        return self.q(css='.Pagination__pagination').present

    ## assuming that we are starting with a page that has elements in it already? (based on exising test setup file)
    @wait_for_js
    def table_element_on_page(self):
        """
        Checks that table is on the page.
        """
        return self.q(css='table.Table__table-responsive').present

    def return_results_set(self):
        """
        Returns the asset set from the page
        """
        return self.q(css="table.Table__table-responsive tr").results
