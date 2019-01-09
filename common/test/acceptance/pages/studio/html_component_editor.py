from common.test.acceptance.pages.studio.utils import type_in_codemirror
from xblock_editor import XBlockEditorView
from common.test.acceptance.pages.common.utils import click_css


class HtmlXBlockEditorView(XBlockEditorView):
    """
    Represents the rendered view of an HTML component editor.
    """

    editor_mode_css = '.edit-xblock-modal .editor-modes .editor-button'
    settings_tab = '.editor-modes .settings-button'
    save_settings_button = '.action-save'

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

    def open_settings_tab(self):
        """
        Clicks settings button on the modal
        """
        click_css(self, self.settings_tab)

    def save_settings(self):
        """
        Click save button on the modal
        """
        click_css(self, self.save_settings_button)

    def open_link_plugin(self):
        """
        Opens up the link plugin on editor
        """
        self.q(css='[aria-label="Insert/edit link"]').click()
        self.wait_for_element_visibility('.mce-window-head', 'Window header present')

    def save_static_link(self, static_link):
        """
        Adds static link inside the link plugin
        """
        self.q(css='.mce-combobox .mce-textbox').fill(static_link)
        self.q(css='.mce-btn.mce-primary').click()

    @property
    def href(self):
        """
        Gets the href from the editor
        """
        return self.q(css="#tinymce>p>a").attrs('href')[0]

    def switch_to_iframe(self):
        """
        Switches to the editor iframe
        """
        self.browser.switch_to_frame(self.browser.find_element_by_tag_name('iframe'))

    @property
    def url_from_the_link_plugin(self):
        """
        Clicks the already set link from the editor and then returns the URL from the link plugin
        """
        self.open_link_plugin()
        return self.browser.execute_script('return $(".mce-textbox").val();')

    def get_default_settings(self):
        """
        Returns default display name and editor
        """
        display_name_setting = self.q(css='.wrapper-comp-setting input[type="text"]:nth-child(2)').attrs('value')[0]
        editor_setting = self.q(css='.wrapper-comp-setting .input.setting-input :nth-child(1)').text[0]
        return [display_name_setting, editor_setting]

    @property
    def keys(self):
        """
        Gets setting keys
        """
        return self.q(css='.label.setting-label[for]').text

    def set_field_val(self, field_display_name, field_value):
        """
        If editing, set the value of a field.
        """
        selector = '.xblock-studio_view li.field label:contains("{}") + input'.format(field_display_name)
        script = "$(arguments[0]).val(arguments[1]).change();"
        self.browser.execute_script(script, selector, field_value)

    def save(self):
        """
        Clicks save button.
        """
        click_css(self, '.save-button')


class HTMLEditorIframe(XBlockEditorView):
    """
    Represent the iframe on HTMl editor view
    """

    def is_browser_on_page(self):
        return self.q(css='#tinymce').present

    @property
    def href(self):
        """
        Gets the href from the editor
        """
        return self.q(css="#tinymce>p>a").attrs('href')[0]

    def select_link(self):
        """
        Clicks the already set link from the editor and then returns the URL from the link plugin
        """
        self.q(css='#tinymce>p>a').first.click()

    def switch_to_default(self):
        """
        Switches to default page

        """
        self.browser.switch_to_default_content()
