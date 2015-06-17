from bok_choy.page_object import PageObject

class PrivacyPolicyPage(PageObject):
    """
    Privacy Policy Page
    """

    url = 'https://guido:vanrossum@www.stage.edx.org/edx-privacy-policy'

    def is_browser_on_page(self):
        return 'edx privacy policy' in self.browser.title.lower()