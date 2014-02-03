"""
Static Pages page for a course.
"""

from .course_page import CoursePage


class StaticPagesPage(CoursePage):
    """
    Static Pages page for a course.
    """

    URL_PATH = "tabs"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-static-pages')
