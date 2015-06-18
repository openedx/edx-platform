from bok_choy.page_object import PageObject
from . import BASE_URL_LMS

class PrivacyPolicyPage(PageObject):
    """
    Privacy Policy Page
    """

    url = BASE_URL_LMS + '/edx-privacy-policy'

    def is_browser_on_page(self):
        return 'edx privacy policy' in self.browser.title.lower()
