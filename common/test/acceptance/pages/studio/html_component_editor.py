"""
HTML component editor in studio
"""


from six.moves import zip

from common.test.acceptance.pages.common.utils import click_css
from common.test.acceptance.pages.studio.utils import get_codemirror_value, type_in_codemirror
from common.test.acceptance.pages.studio.xblock_editor import XBlockEditorView


class HtmlXBlockEditorView(XBlockEditorView):
    """
    Represents the rendered view of an HTML component editor.
    """

    editor_mode_css = '.edit-xblock-modal .editor-modes .editor-button'
    settings_tab = '.editor-modes .settings-button'
    save_settings_button = '.action-save'

    @property
    def toolbar_dropdown_titles(self):
        """
        Returns the titles of dropdowns present on the toolbar
        """
        return self.q(css='.mce-listbox').text

    @property
    def toolbar_button_titles(self):
        """
        Returns the titles of the buttons present on the toolbar
        Returns:

        """
        return self.q(css='.mce-ico').attrs('class')

    @property
    def fonts(self):
        """
        Available fonts in the font dropdown
        Returns:
            (list): A list of font names
        """
        return self.q(css='.mce-text').text

    @property
    def font_families(self):
        """
        Available font families against each font
        Returns:
            (list): A list of font families
        """
        return self.q(css='.mce-text').attrs('style')

    def open_font_dropdown(self):
        """
        Clicks and waits for font dropdown to open
        """
        self.q(css='#mce_2-open').first.click()
        self.wait_for_element_visibility('.mce-floatpanel', 'Dropdown is Visible')

    def font_dict(self):
        """
        Creates a dictionary with font labels and font families
        Returns:
            font_dict(dict): A dictionary of font labels as keys and font families as values
        """
        font_labels = self.fonts
        font_families = self.font_families
        for index, font in enumerate(font_families):
            font = font.replace('font-family: ', '').replace(';', '')
            font_families[index] = font.split(',')
            font_families[index] = [x.lstrip() for x in font_families[index]]
        font_dict = dict(list(zip(font_labels, font_families)))
        return font_dict

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

    def open_raw_editor(self):
        """
        Clicks and waits for raw editor to open
        """
        self.q(css='[aria-label="Edit HTML"]').click()
        self.wait_for_element_visibility('.mce-title', 'Wait for CodeMirror editor')

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

    @property
    def editor_value(self):
        """
        Returns codemirror value from raw HTMl editor
        """
        return get_codemirror_value(self, 0)

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

    def set_text_and_select(self, text):
        """
        Sets and selects text from html editor
        """
        script = """
        var editor = tinyMCE.activeEditor;
        editor.setContent(arguments[0]);
        editor.selection.select(editor.dom.select('p')[0]);"""
        self.browser.execute_script(script, str(text))
        self.wait_for_ajax()

    def click_code_toolbar_button(self):
        """
        Clicks on the code plugin on the toolbar
        """
        self.q(css='.mce-i-none').first.click()

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
        selector = u'.xblock-studio_view li.field label:contains("{}") + input'.format(field_display_name)
        script = "$(arguments[0]).val(arguments[1]).change();"
        self.browser.execute_script(script, selector, field_value)

    def save(self):
        """
        Clicks save button.
        """
        click_css(self, '.save-button')

    def save_content(self):
        """
        Click save button
        """
        click_css(self, '.action-save')

    def open_image_modal(self):
        """
        Clicks and in insert image button
        """
        click_css(self, 'div i[class="mce-ico mce-i-image"]')

    def upload_image(self, file_name):
        """
        Upload image and add description and click save to upload image via TinyMCE editor.
        """
        file_input_css = "[type='file']"

        # select file input element and change visibility to add file.
        self.browser.execute_script('$("{}").css("display","block");'.format(file_input_css))
        self.wait_for_element_visibility(file_input_css, "Input is visible")
        self.q(css=file_input_css).results[0].send_keys(file_name)
        self.wait_for_element_visibility('#imageDescription', 'Upload form is visible.')

        self.q(css='#imageDescription').results[0].send_keys('test image')
        click_css(self, '.modal-footer .btn-primary')


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
