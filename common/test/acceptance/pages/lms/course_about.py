"""
Course about page (with registration button)
"""

from .course_page import CoursePage
from .register import RegisterPage


class CourseAboutPage(CoursePage):
    """
    Course about page (with registration button)
    """

    url_path = "about"

    def is_browser_on_page(self):
        return self.is_css_present('section.course-info')

    def register(self):
        """
        Navigate to the registration page.
        Waits for the registration page to load, then
        returns the registration page object.
        """
        self.css_click('a.register')

        registration_page = RegisterPage(self.browser, self.course_id)
        registration_page.wait_for_page()
        return registration_page
