from bok_choy.page_object import PageObject
from common.test.acceptance.pages.studio import BASE_URL


class SignupPage(PageObject):
    """
    Signup page for Studio.
    """

    url = BASE_URL + "/signup"

    def is_browser_on_page(self):
        return self.q(css='body.view-signup').present
