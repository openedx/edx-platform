"""
Course Advanced Settings page
"""

from .course_page import CoursePage


class AdvancedSettingsPage(CoursePage):
    """
    Course Advanced Settings page.
    """

    url_path = "settings/advanced"

    def is_browser_on_page(self):
        return self.q(css='body.advanced').present
