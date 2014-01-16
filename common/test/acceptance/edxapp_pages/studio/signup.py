from bok_choy.page_object import PageObject
from . import BASE_URL


class SignupPage(PageObject):
    """
    Signup page for Studio.
    """

    url = BASE_URL + "/signup"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-signup')
