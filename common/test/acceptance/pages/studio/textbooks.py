"""
Course Textbooks page.
"""

from .course_page import CoursePage


class TextbooksPage(CoursePage):
    """
    Course Textbooks page.
    """

    url_path = "textbooks"

    def is_browser_on_page(self):
        return self.q(css='body.view-textbooks').present
