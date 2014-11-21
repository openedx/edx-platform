"""
Course Schedule and Details Settings page.
"""

from .course_page import CoursePage
from .utils import press_the_notification_button


class SettingsPage(CoursePage):
    """
    Course Schedule and Details Settings page.
    """

    url_path = "settings/details"

    def is_browser_on_page(self):
        return self.q(css='body.view-settings').present

    @property
    def pre_requisite_course(self):
        """
        Returns the pre-requisite course drop down field.
        """
        return self.q(css='#pre-requisite-course')

    def save_changes(self):
        """
        Clicks save button.
        """
        press_the_notification_button(self, "save")

    def refresh_page(self):
        """
        Reload the page.
        """
        self.browser.refresh()
