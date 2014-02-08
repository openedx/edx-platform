"""
Course Import page.
"""

from .course_page import CoursePage


class ImportPage(CoursePage):
    """
    Course Import page.
    """

    URL_PATH = "import"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-import')
