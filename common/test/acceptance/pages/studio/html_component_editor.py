from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from utils import click_css
from component_editor import ComponentEditorView


class HtmlComponentEditorView(ComponentEditorView):
    """
    Represents the rendered view of an HTML component editor.
    """

    def set_content_and_save(self, content):
        """
        Types content into the html component.
        """
        self.q(css='.edit-xblock-modal .editor-modes .editor-button').click()
        editor = self.q(css=self._bounded_selector('.html-editor .mce-edit-area'))[0]
        ActionChains(self.browser).click(editor).\
            send_keys([Keys.CONTROL, 'a']).key_up(Keys.CONTROL).send_keys(content).perform()
        click_css(self, 'a.action-save')
