"""
Acceptance test xblock-editor.
"""


from bok_choy.page_object import PageObject
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from common.test.acceptance.pages.common.utils import click_css
from common.test.acceptance.tests.helpers import get_selected_option_text, select_option_by_text


class BaseXBlockEditorView(PageObject):
    """
    A base :class:`.PageObject` for the xblock and visibility editors.

    This class assumes that the editor is our default editor as displayed for xmodules.
    """
    BODY_SELECTOR = '.xblock-editor'

    def __init__(self, browser, locator):
        """
        Args:
            browser (selenium.webdriver): The Selenium-controlled browser that this page is loaded in.
            locator (str): The locator that identifies which xblock this :class:`.xblock-editor` relates to.
        """
        super(BaseXBlockEditorView, self).__init__(browser)
        self.locator = locator

    def is_browser_on_page(self):
        return self.q(css='{}[data-locator="{}"]'.format(self.BODY_SELECTOR, self.locator)).present

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular `XBlockEditorView` context
        """
        return u'{}[data-locator="{}"] {}'.format(
            self.BODY_SELECTOR,
            self.locator,
            selector
        )

    def url(self):
        """
        Returns None because this is not directly accessible via URL.
        """
        return None

    def save(self):
        """
        Clicks save button.
        """
        click_css(self, 'a.action-save')

    def cancel(self):
        """
        Clicks cancel button.
        """
        click_css(self, 'a.action-cancel', require_notification=False)


class XBlockEditorView(BaseXBlockEditorView):
    """
    A :class:`.PageObject` representing the rendered view of an xblock editor.
    """
    def get_setting_element(self, label):
        """
        Returns the index of the setting entry with given label (display name) within the Settings modal.
        """
        settings_button = self.q(css='.edit-xblock-modal .editor-modes .settings-button')
        if settings_button.is_present():
            settings_button.click()
        setting_labels = self.q(css=self._bounded_selector('.metadata_edit .wrapper-comp-setting .setting-label'))
        for index, setting in enumerate(setting_labels):
            if setting.text == label:
                return self.q(css=self._bounded_selector('.metadata_edit div.wrapper-comp-setting .setting-input'))[index]
        return None

    def set_field_value_and_save(self, label, value):
        """
        Sets the text field with given label (display name) to the specified value, and presses Save.
        """
        elem = self.get_setting_element(label)

        # Clear the current value, set the new one, then
        # Tab to move to the next field (so change event is triggered).
        elem.clear()
        elem.send_keys(value)
        elem.send_keys(Keys.TAB)
        self.save()

    def set_select_value_and_save(self, label, value):
        """
        Sets the select with given label (display name) to the specified value, and presses Save.
        """
        elem = self.get_setting_element(label)
        select = Select(elem)
        select.select_by_value(value)
        self.save()

    def get_selected_option_text(self, label):
        """
        Returns the text of the first selected option for the select with given label (display name).
        """
        elem = self.get_setting_element(label)
        if elem:
            select = Select(elem)
            return select.first_selected_option.text
        else:
            return None


class XBlockVisibilityEditorView(BaseXBlockEditorView):
    """
    A :class:`.PageObject` representing the rendered view of an xblock visibility editor.
    """
    OPTION_SELECTOR = '.partition-group-control .field'
    ALL_LEARNERS_AND_STAFF = 'All Learners and Staff'
    CONTENT_GROUP_PARTITION = 'Content Groups'
    ENROLLMENT_TRACK_PARTITION = "Enrollment Track Groups"

    @property
    def all_group_options(self):
        """
        Return all partition groups.
        """
        return self.q(css=self._bounded_selector(self.OPTION_SELECTOR)).results

    @property
    def current_groups_message(self):
        """
        This returns the message shown at the top of the visibility dialog about the
        current visibility state (at the time that the dialog was opened).
        For example, "Access is restricted to: All Learners and Staff".
        """
        return self.q(css=self._bounded_selector('.visibility-header'))[0].text

    @property
    def selected_partition_scheme(self):
        """
        Return the selected partition scheme (or "All Learners and Staff"
        if no partitioning is selected).
        """
        selector = self.q(css=self._bounded_selector('.partition-visibility select'))
        return get_selected_option_text(selector)

    def select_partition_scheme(self, partition_name):
        """
        Sets the selected partition scheme to the one with the
        matching name.
        """
        selector = self.q(css=self._bounded_selector('.partition-visibility select'))
        select_option_by_text(selector, partition_name, focus_out=True)

    @property
    def selected_groups(self):
        """
        Return all selected partition groups. If none are selected,
        returns an empty array.
        """
        results = []
        for option in self.all_group_options:
            checkbox = option.find_element_by_css_selector('input')
            if checkbox.is_selected():
                results.append(option)
        return results

    def select_group(self, group_name, save=True):
        """
        Select the first group which has a label matching `group_name`.

        Arguments:
            group_name (str): The name of the group.
            save (boolean): Whether the "save" button should be clicked
                afterwards.
        Returns:
            bool: Whether a group with the provided name was found and clicked.
        """
        for option in self.all_group_options:
            if group_name in option.text:
                checkbox = option.find_element_by_css_selector('input')
                checkbox.click()
                if save:
                    self.save()
                return True
        return False

    def select_groups_in_partition_scheme(self, partition_name, group_names):
        """
        Select groups in the provided partition scheme. The "save"
        button is clicked afterwards.
        """
        self.select_partition_scheme(partition_name)
        for label in group_names:
            self.select_group(label, save=False)
        self.save()
