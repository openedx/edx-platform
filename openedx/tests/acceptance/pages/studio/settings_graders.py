"""
Course Grading Settings page.
"""

from openedx.tests.acceptance.pages.studio.course_page import CoursePage


class GradingPage(CoursePage):
    """
    Course Grading Settings page.
    """

    url_path = "settings/grading"

    def is_browser_on_page(self):
        return self.q(css='body.grading').present
