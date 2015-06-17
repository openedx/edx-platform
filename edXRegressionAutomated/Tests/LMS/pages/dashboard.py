from bok_choy.page_object import PageObject

from Tests.LMS.pages import BASE_URL


class Dashboard(PageObject):
    """
    Dashboard for the pages
    """

    url = BASE_URL

    def is_browser_on_page(self):
        return self.q(css='section.my-courses').present