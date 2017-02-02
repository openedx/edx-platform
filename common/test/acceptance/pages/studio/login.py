"""
Login page for Studio.
"""
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from common.test.acceptance.pages.studio import BASE_URL
from common.test.acceptance.pages.studio.course_page import CoursePage
from common.test.acceptance.pages.studio.utils import HelpMixin


class LoginMixin(object):
    """
    Mixin class used for logging into the system.
    """
    def fill_field(self, css, value):
        """
        Fill the login form field with the value.
        """
        self.q(css=css).fill(value)

    def login(self, email, password, expect_success=True):
        """
        Attempt to log in using 'email' and 'password'.
        """
        self.fill_field('input#email', email)
        self.fill_field('input#password', password)
        self.q(css='button#submit').first.click()

        # Ensure that we make it to another page
        if expect_success:
            EmptyPromise(
                lambda: "signin" not in self.browser.current_url,
                "redirected from the login page"
            ).fulfill()


class LoginPage(PageObject, LoginMixin, HelpMixin):
    """
    Login page for Studio.
    """
    url = BASE_URL + "/signin"

    def is_browser_on_page(self):
        return self.q(css='body.view-signin').visible


class CourseOutlineSignInRedirectPage(CoursePage, LoginMixin):
    """
    Page shown when the user tries to accesses the course while not signed in.
    """
    url_path = "course"

    def is_browser_on_page(self):
        return self.q(css='body.view-signin').visible
