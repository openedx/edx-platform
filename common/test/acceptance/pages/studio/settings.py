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

    def get_elements(self, css_selector):
        self.wait_for_element_presence(
            css_selector,
            'Elements matching "{}" selector are present'.format(css_selector)
        )
        results = self.q(css=css_selector)
        return results

    def get_element(self, css_selector):
        results = self.get_elements(css_selector=css_selector)
        return results[0] if results else None

    @property
    def pre_requisite_course_options(self):
        """
        Returns the pre-requisite course drop down field options.
        """
        return self.get_elements('#pre-requisite-course')

    @property
    def entrance_exam_field(self):
        """
        Returns the enable entrance exam checkbox.
        """
        return self.get_element('#entrance-exam-enabled')

    @property
    def alert_confirmation_title(self):
        """
        Returns the alert confirmation element, which contains text
        such as 'Your changes have been saved.'
        """
        return self.get_element('#alert-confirmation-title')

    def require_entrance_exam(self, required=True):
        """
        Set the entrance exam requirement via the checkbox.
        """
        checkbox = self.entrance_exam_field
        selected = checkbox.is_selected()
        if required and not selected:
            checkbox.click()
            self.wait_for_element_visibility(
                '#entrance-exam-minimum-score-pct',
                'Entrance exam minimum score percent is visible'
            )
        if not required and selected:
            checkbox.click()
            self.wait_for_element_invisibility(
                '#entrance-exam-minimum-score-pct',
                'Entrance exam minimum score percent is invisible'
            )

    def save_changes(self, wait_for_confirmation=True):
        """
        Clicks save button, waits for confirmation unless otherwise specified
        """
        press_the_notification_button(self, "save")
        if wait_for_confirmation:
            self.wait_for_element_visibility(
                '#alert-confirmation-title',
                'Save confirmation message is visible'
            )

    def refresh_page(self, wait_for_confirmation=True):
        """
        Reload the page.
        """
        self.browser.refresh()
        if wait_for_confirmation:
            EmptyPromise(
                lambda: self.q(css='body.view-settings').present,
                'Page is refreshed'
            ).fulfill()
        self.wait_for_ajax()
