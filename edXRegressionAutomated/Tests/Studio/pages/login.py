from bok_choy.page_object import PageObject
from . import BASE_URL
from edgehelp import EdgeHelpPage
from mycoursespage import MyCoursesPage
from signup import SignUpPage

class LoginPage(PageObject):
    """
    pages Login Page
    """

    url = BASE_URL + '/signin'

    def is_browser_on_page(self):
        return self.q(css='body.view-signin').present

    def click_dont_have_studio_account_link(self):
        # Click on Don't have a pages Account? Sign up! link

        self.q(css='.content header a.action.action-signin').first.click()
        SignUpPage(self.browser).wait_for_page()

    def click_our_support_center_link(self):
        # Click on Our Support Center link

        self.q(css='.bit p a').first.click()
        for handle in self.browser.window_handles:
            self.browser.switch_to_window(handle)
        EdgeHelpPage(self.browser).wait_for_page()

    def login(self, email, password):
        """
        Attempt to log in using `email` and `password`.
        """

        self.q(css='input#email').fill(email)
        self.q(css='input#password').fill(password)
        self.q(css='button#submit').first.click()

    def login_success_validation(self):
        # Ensure that we make it to Course Outline page

        MyCoursesPage(self.browser).wait_for_page()

    def login_error_validation(self):
        # Ensure that Authentication error message displays

        self.wait_for_element_presence('#login_error', 'Error message is present')
        self.q(css='#login_error').is_present()
