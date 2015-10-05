from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from component_editor import ComponentEditorView


class HtmlComponentEditorView(ComponentEditorView):
    """
    Represents the rendered view of an HTML component editor.
    """

    editor_mode_css = '.edit-xblock-modal .editor-modes .editor-button'

    def set_content_and_save(self, content, raw=False):
        """Types content into the html component and presses Save.

        Arguments:
            content (str): The content to be used.
            raw (bool): If true, edits in 'raw HTML' mode.
        """
        if raw:
            self.set_raw_content(content)
        else:
            self.set_content(content)

        self.save()

    def set_content_and_cancel(self, content, raw=False):
        """Types content into the html component and presses Cancel to abort.

        Arguments:
            content (str): The content to be used.
            raw (bool): If true, edits in 'raw HTML' mode.
        """
        if raw:
            self.set_raw_content(content)
        else:
            self.set_content(content)

        self.cancel()

    def set_content(self, content):
        """Types content into the html component, leaving the component open.

        Arguments:
            content (str): The content to be used.
        """
        self.q(css=self.editor_mode_css).click()

        selector = '.html-editor .mce-edit-area'
        editor = self.q(css=self._bounded_selector(selector))[0]
        ActionChains(self.browser).click(editor).\
            send_keys([Keys.CONTROL, 'a']).key_up(Keys.CONTROL).\
            send_keys(content).perform()

    def set_raw_content(self, content):
        """Types content in raw html mode, leaving the component open.

        Arguments:
            content (str): The content to be used.
        """
        self.q(css=self.editor_mode_css).click()
        self.q(css='[aria-label="Edit HTML"]').click()

        #Focus goes to the editor by default
        ActionChains(self.browser).send_keys([Keys.CONTROL, 'a']).\
            key_up(Keys.CONTROL).send_keys(content).perform()

        self.q(css='.mce-foot .mce-primary').click()
