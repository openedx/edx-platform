"""
Library Content XBlock Wrapper
"""
from bok_choy.page_object import PageObject


class LibraryContentXBlockWrapper(PageObject):
    """
    A PageObject representing a wrapper around a LibraryContent block seen in the LMS
    """
    url = None
    BODY_SELECTOR = '.xblock-student_view div'

    def __init__(self, browser, locator):
        super(LibraryContentXBlockWrapper, self).__init__(browser)
        self.locator = locator

    def is_browser_on_page(self):
        """
        Checks if page is opened
        """
        return self.q(css='{}[data-id="{}"]'.format(self.BODY_SELECTOR, self.locator)).present

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular block's context
        """
        return '{}[data-id="{}"] {}'.format(
            self.BODY_SELECTOR,
            self.locator,
            selector
        )

    @property
    def children_contents(self):
        """
        Gets contents of all child XBlocks as list of strings
        """
        child_blocks = self.q(css=self._bounded_selector("div[data-id]"))
        return frozenset(child.text for child in child_blocks)

    @property
    def children_headers(self):
        """
        Gets headers of all child XBlocks as list of strings
        """
        child_blocks_headers = self.q(css=self._bounded_selector("div[data-id] h3.problem-header"))
        return frozenset(child.text for child in child_blocks_headers)
