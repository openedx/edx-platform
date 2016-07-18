"""
Home page for Studio when not logged in.
"""

from bok_choy.page_object import PageObject
from common.test.acceptance.pages.studio import BASE_URL


class HowitworksPage(PageObject):
    """
    Home page for Studio when not logged in.
    """

    url = BASE_URL + "/howitworks"

    def is_browser_on_page(self):
        return self.q(css='body.view-howitworks').present
