"""
Login page for Studio.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from . import BASE_URL


class LoginPage(PageObject):
    """
    Login page for Studio.
    """

    url = BASE_URL + "/signin"

    def is_browser_on_page(self):
        return self.q(css='body.view-signin').present

    def login(self, email, password):
        """
        Attempt to log in using `email` and `password`.
        """

        # Ensure that we make it to another page
        on_next_page = EmptyPromise(
            lambda: "login" not in self.browser.url,
            "redirected from the login page"
        )

        with fulfill_after(on_next_page):
            self.css_fill('input#email', email)
            self.css_fill('input#password', password)
            self.css_click('button#submit')
