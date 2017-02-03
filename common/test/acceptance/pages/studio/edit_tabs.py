"""
Pages page for a course.
"""

from common.test.acceptance.pages.studio.course_page import CoursePage


class PagesPage(CoursePage):
    """
    Pages page for a course.
    """

    url_path = "tabs"

    def is_browser_on_page(self):
        return self.q(css='body.view-static-pages').present
