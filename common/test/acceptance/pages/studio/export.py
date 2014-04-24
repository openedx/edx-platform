"""
Course Export page.
"""

from .course_page import CoursePage


class ExportPage(CoursePage):
    """
    Course Export page.
    """

    url_path = "export"

    def is_browser_on_page(self):
        return self.q(css='body.view-export').present
