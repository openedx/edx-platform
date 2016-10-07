"""
Find courses page (main page of the LMS).
"""

from bok_choy.page_object import PageObject
from openedx.tests.acceptance.pages.lms import BASE_URL


class FindCoursesPage(PageObject):
    """
    Find courses page (main page of the LMS).
    """

    url = BASE_URL

    def is_browser_on_page(self):
        return "edX" in self.browser.title

    @property
    def course_id_list(self):
        """
        Retrieve the list of available course IDs
        on the page.
        """

        return self.q(css='article.course').attrs('id')
