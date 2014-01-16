"""
Find courses page (main page of the LMS).
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import BrokenPromise
from . import BASE_URL


class FindCoursesPage(PageObject):
    """
    Find courses page (main page of the LMS).
    """

    url = BASE_URL

    def is_browser_on_page(self):
        return self.browser.title == "edX"

    @property
    def course_id_list(self):
        """
        Retrieve the list of available course IDs
        on the page.
        """
        return self.css_map('article.course', lambda el: el['id'])
