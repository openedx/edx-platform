from component_editor import ComponentEditorView
from openedx.tests.acceptance.pages.studio.utils import type_in_codemirror


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
        """Sets content in the html component, leaving the component open.

        Arguments:
            content (str): The content to be used.
        """
        self.q(css=self.editor_mode_css).click()
        self.browser.execute_script("tinyMCE.activeEditor.setContent('%s')" % content)

    def set_raw_content(self, content):
        """Types content in raw html mode, leaving the component open.
        Arguments:
            content (str): The content to be used.
        """
        self.q(css=self.editor_mode_css).click()
        self.q(css='[aria-label="Edit HTML"]').click()
        self.wait_for_element_visibility('.mce-title', 'Wait for CodeMirror editor')
        # Set content in the CodeMirror editor.
        type_in_codemirror(self, 0, content)

        self.q(css='.mce-foot .mce-primary').click()
