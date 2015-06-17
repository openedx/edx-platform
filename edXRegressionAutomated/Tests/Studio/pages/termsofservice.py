from bok_choy.page_object import PageObject

class TermsOfServicePage(PageObject):
    """
    Terms of Service Page
    """

    url = 'https://guido:vanrossum@www.stage.edx.org/edx-terms-service'

    def is_browser_on_page(self):
        return 'edx terms of service' in self.browser.title.lower()