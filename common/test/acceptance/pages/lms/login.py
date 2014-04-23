"""
Login page for the LMS.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise
from . import BASE_URL
from .dashboard import DashboardPage


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
        self.provide_info(email, password)
        self.submit()

    def provide_info(self, email, password):
        """
        Fill in login info.
        `email` and `password` are the user's credentials.
        """
        EmptyPromise(self.q(css='input#email').is_present, "Click ready").fulfill()
        EmptyPromise(self.q(css='input#password').is_present, "Click ready").fulfill()

        self.q(css='input#email').fill(email)
        self.q(css='input#password').fill(password)
        self.wait_for_ajax()

    def submit(self):
        """
        Submit registration info to create an account.
        """
        self.q(css='button#submit').first.click()

        # The next page is the dashboard; make sure it loads
        dashboard = DashboardPage(self.browser)
        dashboard.wait_for_page()
        return dashboard
