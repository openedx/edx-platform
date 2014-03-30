"""
Container page in Studio
"""

from bok_choy.page_object import PageObject

from . import BASE_URL


class ContainerPage(PageObject):
    """
    Container page in Studio
    """

    def __init__(self, browser, unit_locator):
        super(ContainerPage, self).__init__(browser)
        self.unit_locator = unit_locator

    @property
    def url(self):
        """URL to the container page for an xblock."""
        return "{}/container/{}".format(BASE_URL, self.unit_locator)

    def is_browser_on_page(self):
        # Wait until all components have been loaded
        return (
            self.q(css='body.view-container').present and
            len(self.q(css=XBlockWrapper.BODY_SELECTOR).results) == len(
                self.q(css='{} .xblock'.format(XBlockWrapper.BODY_SELECTOR)).results)
        )

    @property
    def xblocks(self):
        """
        Return a list of xblocks loaded on the container page.
        """
        return self.q(css=XBlockWrapper.BODY_SELECTOR).map(
            lambda el: XBlockWrapper(self.browser, el.get_attribute('data-locator'))).results


class XBlockWrapper(PageObject):
    """
    A PageObject representing a wrapper around an XBlock child shown on the Studio container page.
    """
    url = None
    BODY_SELECTOR = '.wrapper-xblock'
    NAME_SELECTOR = '.header-details'

    def __init__(self, browser, locator):
        super(XBlockWrapper, self).__init__(browser)
        self.locator = locator

    def is_browser_on_page(self):
        return self.q(css='{}[data-locator="{}"]'.format(self.BODY_SELECTOR, self.locator)).present

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular `CourseOutlineChild` context
        """
        return '{}[data-locator="{}"] {}'.format(
            self.BODY_SELECTOR,
            self.locator,
            selector
        )

    @property
    def name(self):
        titles = self.q(css=self._bounded_selector(self.NAME_SELECTOR)).text
        if titles:
            return titles[0]
        else:
            return None

    @property
    def preview_selector(self):
        return self._bounded_selector('.xblock-student_view')
