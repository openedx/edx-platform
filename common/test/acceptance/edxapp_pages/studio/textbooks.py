"""
Course Textbooks page.
"""

from .course_page import CoursePage


class TextbooksPage(CoursePage):
    """
    Course Textbooks page.
    """

    URL_PATH = "textbooks"

    def is_browser_on_page(self):
        return self.is_css_present('body.view-textbooks')
