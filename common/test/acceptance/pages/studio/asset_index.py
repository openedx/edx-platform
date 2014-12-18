"""
The Files and Uploads page for a course in Studio
"""

import time
from .course_page import CoursePage
from bok_choy.javascript import wait_for_js, js_defined, requirejs
from bok_choy.promise import EmptyPromise


@requirejs('js/views/assets')
class AssetIndexPage(CoursePage):

    """
    The Files and Uploads page for a course in Studio
    """

    url_path = "assets"
    type_filter_element = '#js-asset-type-col'

    @wait_for_js
    def is_browser_on_page(self):
        return self.q(css='body.view-uploads').present

    @wait_for_js
    def type_filter_on_page(self):
        """
        Checks that type filter is in table header.
        """
        return self.q(css=self.type_filter_element).present

    def type_filter_header_label_visible(self):
        """
        Checks type filter label is added and visible in the pagination header.
        """
        return self.q(css='span.filter-column').visible

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
            self.wait_for_element_visibility(self.type_filter_element + " .wrapper-nav-sub", "Type Filter promise satisfied.")
            self.q(css=self.type_filter_element + " .column-filter-link").nth(filter_number).click()
            self.wait_for_ajax()
            return True
        return False

    def return_results_set(self):
        """
        Returns the asset set from the page
        """
        return self.q(css="#asset-table-body tr").results
