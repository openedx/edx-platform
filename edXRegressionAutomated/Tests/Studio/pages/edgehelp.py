from bok_choy.page_object import PageObject


class EdgeHelpPage(PageObject):
    """
    Edge Help Page
    """

    url = None

    def is_browser_on_page(self):
        return 'edx studio support' in self.browser.title.lower()