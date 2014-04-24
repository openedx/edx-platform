"""
Course Schedule and Details Settings page.
"""

from .course_page import CoursePage


class SettingsPage(CoursePage):
    """
    Course Schedule and Details Settings page.
    """

    url_path = "settings/details"

    def is_browser_on_page(self):
        return self.q(css='body.view-settings').present
