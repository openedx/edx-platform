from bok_choy.page_object import PageObject
from ..studio import BASE_URL


class HowitworksPage(PageObject):
    """
    Home page for Studio when not logged in.
    """

    @property
    def name(self):
        return "studio.howitworks"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self):
        return BASE_URL + "/howitworks"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-howitworks')
