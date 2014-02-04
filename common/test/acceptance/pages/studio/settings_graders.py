"""
Course Grading Settings page.
"""

from .course_page import CoursePage


class GradingPage(CoursePage):
    """
    Course Grading Settings page.
    """

    URL_PATH = "settings/grading"

    def is_browser_on_page(self):
        return self.is_css_present('body.grading')
