from bok_choy.page_object import PageObject

class HowStudioWorksPage(PageObject):
    """
    How pages Works (Help) page
    """
    url = None

    def is_browser_on_page(self):
        return self.q(css='body.section-dashboard').present
