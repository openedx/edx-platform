"""
Course Schedule and Details Settings page.
"""
from bok_choy.promise import EmptyPromise

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

    @property
    def entrance_exam_field(self):
        """
        Returns the enable entrance exam checkbox.
        """
        return self.q(css='#entrance-exam-enabled')

    def save_changes(self, wait_for_confirmation=True):
        """
        Clicks save button, waits for confirmation unless otherwise specified
        """
        press_the_notification_button(self, "save")
        if wait_for_confirmation:
            EmptyPromise(
                lambda: self.q(css='#alert-confirmation-title').present,
                'Waiting for save confirmation...'
            ).fulfill()

    def refresh_page(self):
        """
        Reload the page.
        """
        self.browser.refresh()
