"""
Login page for Studio.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from common.test.acceptance.pages.studio import BASE_URL


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

        self.q(css='input#email').fill(email)
        self.q(css='input#password').fill(password)
        self.q(css='button#submit').first.click()

        # Ensure that we make it to another page
        EmptyPromise(
            lambda: "login" not in self.browser.current_url,
            "redirected from the login page"
        ).fulfill()
