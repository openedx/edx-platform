from bok_choy.page_object import PageObject


class StudioHelpPage(PageObject):
    """
    read the docs pages Help page
    """
    url = None

    def is_browser_on_page(self):
        return 'getting started with studio' in self.browser.title.lower()
