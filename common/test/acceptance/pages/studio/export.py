"""
Course Export page.
"""

from .course_page import CoursePage
from utils import click_css


class ExportPage(CoursePage):
    """
    Course Export page.
    """

    url_path = "export"

    def is_browser_on_page(self):
        return self.q(css='body.view-export').present

    def click_export_button(self):
        """
        Clicks export button.
        """
        click_css(self, "a.action-export")
