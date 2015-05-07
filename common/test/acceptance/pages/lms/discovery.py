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
        return "Courses" in self.browser.title

    def search(self, string):
        """
        Search and return results
        """
        self.q(css=self.form + ' input[type="text"]').fill(string)
        self.q(css=self.form + ' [type="submit"]').click()
        self.wait_for_ajax()
        return self.q(css=".courses-listing-item")
