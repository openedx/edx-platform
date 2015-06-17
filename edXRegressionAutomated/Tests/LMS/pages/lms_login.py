from bok_choy.page_object import PageObject

from Tests.LMS.pages import BASE_URL
from Tests.LMS.pages.dashboard import Dashboard


class LMSLoginPage(PageObject):
    """
    Login Page for the pages
    """

    url = BASE_URL + "/login"

    def is_browser_on_page(self):
        return self.q(css='.login-button').present

    def login(self, email, password):
        #Attempt to log in using `email` and `password`.

        self.q(css='input#login-email').fill(email)
        self.q(css='input#login-password').fill(password)
        self.q(css='.login-button').first.click()

    def login_success_validation(self):
        # Ensure that we make it to Dashboard Page

        Dashboard(self.browser).wait_for_page()