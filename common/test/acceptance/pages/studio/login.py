"""
Login page for Studio.
"""
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from common.test.acceptance.pages.studio import LMS_URL
from common.test.acceptance.pages.studio.course_page import CoursePage
from common.test.acceptance.pages.studio.utils import HelpMixin


class LoginMixin(object):
    """
    Mixin class used for logging into the system.
    """
    def fill_password(self, password):
        """
        Fill the password field with the value.
        """
        self.q(css="#login-password").fill(password)

    def login(self, email, password, expect_success=True):
        """
        Attempt to log in using 'email' and 'password'.
        """
        self.wait_for_element_visibility('#login-email', 'Email field is shown')
        self.q(css="#login-email").fill(email)
        self.fill_password(password)
        self.q(css=".login-button").click()

        # Ensure that we make it to another page
        if expect_success:
            EmptyPromise(
                lambda: "login" not in self.browser.current_url,
                "redirected from the login page"
            ).fulfill()


class LoginPage(PageObject, LoginMixin, HelpMixin):
    """
    Login page for Studio.
    """
    url = LMS_URL + "/login"

    def is_browser_on_page(self):
        return (
            self.q(css="#login-anchor").is_present() and
            self.q(css=".login-button").visible
        )


class CourseOutlineSignInRedirectPage(CoursePage, LoginMixin):
    """
    Page shown when the user tries to access the course while not signed in.
    """
    url_path = "course"

    def is_browser_on_page(self):
        return self.q(css=".login-button").visible
