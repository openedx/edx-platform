"""
Course discovery page.
"""

from . import BASE_URL
from bok_choy.page_object import PageObject


class CourseDiscoveryPage(PageObject):
    """
    Find courses page (main page of the LMS).
    """

    url = BASE_URL + "/courses"
    form = "#discovery-form"

    def is_browser_on_page(self):
        """
        Loading indicator must be present, but not visible
        """
        loading_css = "#loading-indicator"
        courses_css = '.courses-listing'

        return self.q(css=courses_css).visible \
            and self.q(css=loading_css).present \
            and not self.q(css=loading_css).visible

    @property
    def result_items(self):
        """
        Return search result items.
        """
        return self.q(css=".courses-listing-item")

    @property
    def clear_button(self):
        """
        Clear all button.
        """
        return self.q(css="#clear-all-filters")

    def search(self, string):
        """
        Search and wait for ajax.
        """
        self.q(css=self.form + ' input[type="text"]').fill(string)
        self.q(css=self.form + ' [type="submit"]').click()
        self.wait_for_ajax()

    def clear_search(self):
        """
        Clear search results.
        """
        self.clear_button.click()
        self.wait_for_ajax()
