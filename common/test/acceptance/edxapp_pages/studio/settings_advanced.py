"""
Course Advanced Settings page
"""

from .course_page import CoursePage


class AdvancedSettingsPage(CoursePage):
    """
    Course Advanced Settings page.
    """

    URL_PATH = "settings/advanced"

    def is_browser_on_page(self):
        return self.is_css_present('body.advanced')
