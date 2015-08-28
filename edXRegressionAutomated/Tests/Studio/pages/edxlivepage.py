from bok_choy.page_object import PageObject

class EdxLivePage(PageObject):
    """
    EDX Live Website
    """
    url = None

    def is_browser_on_page(self):
        return 'edx | free online courses' in self.browser.title.lower()
