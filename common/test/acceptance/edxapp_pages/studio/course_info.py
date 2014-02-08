"""
Course Updates page.
"""

from .course_page import CoursePage


class CourseUpdatesPage(CoursePage):
    """
    Course Updates page.
    """

    URL_PATH = "course_info"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-updates')
