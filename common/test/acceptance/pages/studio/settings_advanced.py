"""
Course Advanced Settings page
"""

from .course_page import CoursePage
from .utils import press_the_notification_button, type_in_codemirror, get_codemirror_value


KEY_CSS = '.key h3.title'
UNDO_BUTTON_SELECTOR = ".action-item .action-undo"
MANUAL_BUTTON_SELECTOR = ".action-item .action-cancel"
MODAL_SELECTOR = ".validation-error-modal-content"
ERROR_ITEM_NAME_SELECTOR = ".error-item-title strong"
ERROR_ITEM_CONTENT_SELECTOR = ".error-item-message"

class AdvancedSettingsPage(CoursePage):
    """
    Course Advanced Settings page.
    """

    url_path = "settings/advanced"

    def is_browser_on_page(self):
        return self.q(css='body.advanced').present

    def wait_for_modal_load(self):
        """
        Wait for validation response from the server, and make sure that
        the validation error modal pops up.

        This method should only be called when it is guaranteed that there're
        validation errors in the settings changes.
        """
        self.wait_for_ajax()
        self.wait_for_element_presence(MODAL_SELECTOR, 'Validation Modal is present')

    def refresh_and_wait_for_load(self):
        """
        Refresh the page and wait for all resources to load.
        """
        self.browser.refresh()
        self.wait_for_page()

    def undo_changes_via_modal(self):
        """
        Trigger clicking event of the undo changes button in the modal.
        Wait for the undoing process to load via ajax call.
        """
        self.q(css=UNDO_BUTTON_SELECTOR).click()
        self.wait_for_ajax()

    def trigger_manual_changes(self):
        """
        Trigger click event of the manual changes button in the modal.
        No need to wait for any ajax.
        """
        self.q(css=MANUAL_BUTTON_SELECTOR).click()

    def is_validation_modal_present(self):
        """
        Checks if the validation modal is present.
        """
        return self.q(css=MODAL_SELECTOR).present

    def get_error_item_names(self):
        """
        Returns a list of display names of all invalid settings.
        """
        return self.q(css=ERROR_ITEM_NAME_SELECTOR).text

    def get_error_item_messages(self):
        """
        Returns a list of error messages of all invalid settings.
        """
        return self.q(css=ERROR_ITEM_CONTENT_SELECTOR).text

    def _get_index_of(self, expected_key):
        for i, element in enumerate(self.q(css=KEY_CSS)):
            # Sometimes get stale reference if I hold on to the array of elements
            key = self.q(css=KEY_CSS).nth(i).text[0]
            if key == expected_key:
                return i

        return -1

    def save(self):
        press_the_notification_button(self, "Save")

    def cancel(self):
        press_the_notification_button(self, "Cancel")

    def set(self, key, new_value):
        index = self._get_index_of(key)
        type_in_codemirror(self, index, new_value)
        self.save()

    def get(self, key):
        index = self._get_index_of(key)
        return get_codemirror_value(self, index)

    def set_values(self, key_value_map):
        """
        Make multiple settings changes and save them.
        """
        for key, value in key_value_map.iteritems():
            index = self._get_index_of(key)
            type_in_codemirror(self, index, value)

        self.save()

    def get_values(self, key_list):
        """
        Get a key-value dictionary of all keys in the given list.
        """
        result_map = {}

        for key in key_list:
            index = self._get_index_of(key)
            val = get_codemirror_value(self, index)
            result_map[key] = val

        return result_map
