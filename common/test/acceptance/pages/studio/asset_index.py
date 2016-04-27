"""
The Files and Uploads page for a course in Studio
"""

import urllib
import os
from opaque_keys.edx.locator import CourseLocator
from . import BASE_URL
from .course_page import CoursePage
from bok_choy.javascript import wait_for_js, requirejs


@requirejs('js/views/assets')
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
