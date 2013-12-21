from bok_choy.page_object import PageObject
from ..studio import BASE_URL


class SignupPage(PageObject):
    """
    Signup page for Studio.
    """

    @property
    def name(self):
        return "studio.signup"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self):
        return BASE_URL + "/signup"

    def is_browser_on_page(self):
        return self.browser.title == 'Sign Up | edX Studio'
