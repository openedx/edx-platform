from bok_choy.page_object import PageObject
from . import BASE_URL

class LMSHomePage(PageObject):
    """
    pages Home Page
    """

    url = BASE_URL

    def is_browser_on_page(self):
        return "free online courses " in self.browser.title.lower()
