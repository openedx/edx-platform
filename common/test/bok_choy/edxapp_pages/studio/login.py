from bok_choy.page_object import PageObject
from ..studio import BASE_URL


class LoginPage(PageObject):
    """
    Login page for Studio.
    """

    @property
    def name(self):
        return "studio.login"

    @property
    def requirejs(self):
        return []

    @property
    def js_globals(self):
        return []

    def url(self):
        return BASE_URL + "/signin"

    def is_browser_on_page(self):
        return self.browser.title == 'Sign In | edX Studio'

    def login(self, email, password):
        """
        Attempt to log in using `email` and `password`.
        """
        self.css_fill('input#email', email)
        self.css_fill('input#password', password)
        self.css_click('button#submit')
