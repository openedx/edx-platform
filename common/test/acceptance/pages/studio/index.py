"""
My Courses page in Studio
"""

from bok_choy.page_object import PageObject
from . import BASE_URL


class DashboardPage(PageObject):
    """
    My Courses page in Studio
    """

    url = BASE_URL + "/course/"

    def is_browser_on_page(self):
        return self.q(css='body.view-dashboard').present
