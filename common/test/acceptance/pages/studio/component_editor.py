from bok_choy.page_object import PageObject
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from utils import click_css


class ComponentEditorView(PageObject):
    """
    A :class:`.PageObject` representing the rendered view of a component editor.

    This class assumes that the editor is our default editor as displayed for xmodules.
    """
    BODY_SELECTOR = '.xblock-editor'

    def __init__(self, browser, locator):
        """
        Args:
            browser (selenium.webdriver): The Selenium-controlled browser that this page is loaded in.
            locator (str): The locator that identifies which xblock this :class:`.xblock-editor` relates to.
        """
        super(ComponentEditorView, self).__init__(browser)
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

    def get_setting_entry_index(self, label):
        """
        Returns the index of the setting entry with given label (display name) within the Settings modal.
        """
        # TODO: will need to handle tabbed "Settings" in future (current usage is in vertical, only shows Settings.
        setting_labels = self.q(css=self._bounded_selector('.metadata_edit .wrapper-comp-setting .setting-label'))
        for index, setting in enumerate(setting_labels):
            if setting.text == label:
                return index
        return None

    def set_field_value_and_save(self, label, value):
        """
        Set the field with given label (display name) to the specified value, and presses Save.
        """
        index = self.get_setting_entry_index(label)
        elem = self.q(css=self._bounded_selector('.metadata_edit div.wrapper-comp-setting input.setting-input'))[index]
        # Click in the field, delete the value there.
        action = ActionChains(self.browser).click(elem)
        for _x in range(0, len(elem.get_attribute('value'))):
            action = action.send_keys(Keys.BACKSPACE)
        # Send the new text, then Tab to move to the next field (so change event is triggered).
        action.send_keys(value).send_keys(Keys.TAB).perform()
        click_css(self, 'a.action-save')
