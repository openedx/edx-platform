"""
Course Advanced Settings page
"""

from .course_page import CoursePage
from .utils import press_the_notification_button, type_in_codemirror, get_codemirror_value


KEY_CSS = '.key h3.title'


class AdvancedSettingsPage(CoursePage):
    """
    Course Advanced Settings page.
    """

    url_path = "settings/advanced"

    def is_browser_on_page(self):
        return self.q(css='body.advanced').present

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
