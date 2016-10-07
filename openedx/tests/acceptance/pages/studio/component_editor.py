from bok_choy.page_object import PageObject
from selenium.webdriver.common.keys import Keys
from openedx.tests.acceptance.pages.common.utils import click_css
from selenium.webdriver.support.ui import Select


class BaseComponentEditorView(PageObject):
    """
    A base :class:`.PageObject` for the component and visibility editors.

    This class assumes that the editor is our default editor as displayed for xmodules.
    """
    BODY_SELECTOR = '.xblock-editor'

    def __init__(self, browser, locator):
        """
        Args:
            browser (selenium.webdriver): The Selenium-controlled browser that this page is loaded in.
            locator (str): The locator that identifies which xblock this :class:`.xblock-editor` relates to.
        """
        super(BaseComponentEditorView, self).__init__(browser)
        self.locator = locator

    def is_browser_on_page(self):
        return self.q(css='{}[data-locator="{}"]'.format(self.BODY_SELECTOR, self.locator)).present

    def _bounded_selector(self, selector):
        """
        Return `selector`, but limited to this particular `ComponentEditorView` context
        """
        return '{}[data-locator="{}"] {}'.format(
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


class ComponentEditorView(BaseComponentEditorView):
    """
    A :class:`.PageObject` representing the rendered view of a component editor.
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


class ComponentVisibilityEditorView(BaseComponentEditorView):
    """
    A :class:`.PageObject` representing the rendered view of a component visibility editor.
    """
    OPTION_SELECTOR = '.modal-section-content .field'

    @property
    def all_options(self):
        """
        Return all visibility options.
        """
        return self.q(css=self._bounded_selector(self.OPTION_SELECTOR)).results

    @property
    def selected_options(self):
        """
        Return all selected visibility options.
        """
        results = []
        for option in self.all_options:
            button = option.find_element_by_css_selector('input.input')
            if button.is_selected():
                results.append(option)
        return results

    def select_option(self, label_text, save=True):
        """
        Click the first option which has a label matching `label_text`.

        Arguments:
            label_text (str): Text of a label accompanying the input
                which should be clicked.
            save (boolean): Whether the "save" button should be clicked
                afterwards.
        Returns:
            bool: Whether the label was found and clicked.
        """
        for option in self.all_options:
            if label_text in option.text:
                option.click()
                if save:
                    self.save()
                return True
        return False
