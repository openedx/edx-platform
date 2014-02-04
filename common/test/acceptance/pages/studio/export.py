"""
Course Export page.
"""

from .course_page import CoursePage


class ExportPage(CoursePage):
    """
    Course Export page.
    """

    URL_PATH = "export"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-export')
