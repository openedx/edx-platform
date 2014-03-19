"""
Login page for the LMS.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from . import BASE_URL


class LoginPage(PageObject):
    """
    Login page for the LMS.
    """

    url = BASE_URL + "/login"

    def is_browser_on_page(self):
        return any([
            'log in' in title.lower()
            for title in self.q(css='span.title-super').text
        ])

    def login(self, email, password):
        """
        Attempt to log in using `email` and `password`.
        """

        EmptyPromise(self.q(css='input#email').is_present, "Click ready").fulfill()
        EmptyPromise(self.q(css='input#password').is_present, "Click ready").fulfill()
        
        self.q(css='input#email').fill(email)
        self.q(css='input#password').fill(password)
        self.q(css='button#submit').click()

        EmptyPromise(
            lambda: "login" not in self.browser.url,
            "redirected from the login page"
        )

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

"""
