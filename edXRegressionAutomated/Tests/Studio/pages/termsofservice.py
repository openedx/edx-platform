from bok_choy.page_object import PageObject
from . import BASE_URL_LMS

class TermsOfServicePage(PageObject):
    """
    Terms of Service Page
    """

    url = BASE_URL_LMS + '/edx-terms-service'

    def is_browser_on_page(self):
        return 'edx terms of service' in self.browser.title.lower()
