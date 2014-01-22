"""
Registration page (create a new account)
"""

from bok_choy.page_object import PageObject
from . import BASE_URL


class RegisterPage(PageObject):
    """
    Registration page (create a new account)
    """

    name = "lms.register"

    def url(self, course_id=None):  #pylint: disable=W0221
        """
        URL for the registration page of a course.
        Course ID is currently of the form "edx/999/2013_Spring"
        but this format could change.
        """
        if course_id is None:
            raise NotImplementedError("Must provide a course ID to access about page")

        return BASE_URL + "/register?course_id=" + course_id + "&enrollment_action=enroll"

    def is_browser_on_page(self):
        return any([
            'register' in title.lower()
            for title in self.css_text('span.title-sub')
        ])

    def provide_info(self, credentials):
        """
        Fill in registration info.

        `credentials` is a `TestCredential` object.
        """
        self.css_fill('input#email', credentials.email)
        self.css_fill('input#password', credentials.password)
        self.css_fill('input#username', credentials.username)
        self.css_fill('input#name', credentials.full_name)
        self.css_check('input#tos-yes')
        self.css_check('input#honorcode-yes')

    def submit(self):
        """
        Submit registration info to create an account.
        """
        self.css_click('button#submit')
