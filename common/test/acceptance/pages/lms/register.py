"""
Registration page (create a new account)
"""

from bok_choy.page_object import PageObject
from . import BASE_URL
from .dashboard import DashboardPage


class RegisterPage(PageObject):
    """
    Registration page (create a new account)
    """

    def __init__(self, browser, course_id):
        """
        Course ID is currently of the form "edx/999/2013_Spring"
        but this format could change.
        """
        super(RegisterPage, self).__init__(browser)
        self._course_id = course_id

    @property
    def url(self):
        """
        URL for the registration page of a course.
        """
        return "{base}/register?course_id={course_id}&enrollment_action={action}".format(
            base=BASE_URL,
            course_id=self._course_id,
            action="enroll",
        )

    def is_browser_on_page(self):
        return any([
            'register' in title.lower()
            for title in self.css_text('span.title-sub')
        ])

    def provide_info(self, email, password, username, full_name):
        """
        Fill in registration info.
        `email`, `password`, `username`, and `full_name` are the user's credentials.
        """
        self.css_fill('input#email', email)
        self.css_fill('input#password', password)
        self.css_fill('input#username', username)
        self.css_fill('input#name', full_name)
        self.css_check('input#tos-yes')
        self.css_check('input#honorcode-yes')

    def submit(self):
        """
        Submit registration info to create an account.
        """
        self.css_click('button#submit')

        # The next page is the dashboard; make sure it loads
        dashboard = DashboardPage(self.browser)
        dashboard.wait_for_page()
        return dashboard
