from component_editor import ComponentEditorView
from common.test.acceptance.pages.studio.utils import \
    get_input_value, set_input_value, type_in_codemirror,  get_codemirror_value
from common.test.acceptance.pages.common.utils import click_css
from selenium.webdriver.common.keys import Keys
from collections import OrderedDict
import time


class HtmlComponentEditorView(ComponentEditorView):
    """
    Represents the rendered view of an HTML component editor.
    """

    editor_mode_css = '.edit-xblock-modal .editor-modes .editor-button'
    expected_buttons = [
        'bold',
        'italic',
        'underline',
        'forecolor',
        # This is our custom "code style" button, which uses an image instead of a class.
        'none',
        'bullist',
        'numlist',
        'outdent',
        'indent',
        'blockquote',
        'link',
        'unlink',
        'image'
    ]

    TINYMCE_FONTS = OrderedDict([
        ("Andale Mono", "'andale mono', times"),
        ("Arial", "arial, helvetica, sans-serif"),
        ("Arial Black", "'arial black', 'avant garde'"),
        ("Book Antiqua", "'book antiqua', palatino"),
        ("Comic Sans MS", "'comic sans ms', sans-serif"),
        ("Courier New", "'courier new', courier"),
        ("Georgia", "georgia, palatino"),
        ("Helvetica", "helvetica"),
        ("Impact", "impact, chicago"),
        ("Symbol", "symbol"),
        ("Tahoma", "tahoma, arial, helvetica, sans-serif"),
        ("Terminal", "terminal, monaco"),
        ("Times New Roman", "'times new roman', times"),
        ("Trebuchet MS", "'trebuchet ms', geneva"),
        ("Verdana", "verdana, geneva"),
        # tinyMCE does not set font-family on dropdown span for these two fonts
        ("Webdings", ""),  # webdings
        ("Wingdings", ""),  # wingdings, 'zapf dingbats'
    ])

    CUSTOM_FONTS = OrderedDict([
        ('Default', "'Open Sans', Verdana, Arial, Helvetica, sans-serif"),
    ])

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
        If editing, click on the "Settings" tab
        """
        click_css(self, '.editor-modes .settings-button', require_notification=False)

    def get_edit_html_component_field_values(self):
        """
        Returns setting values.
        """
        setting_values = []
        display_name = self.q(css='.input.setting-input[type="text"]').attrs('value')[0]
        editor = self.q(css='.input.setting-input option[value]').attrs('value')[0]
        for value in [display_name, editor]:
            setting_values.append(value)
        return setting_values

    def save_settings(self):
        """
        Click on settings Save button.
        """
        click_css(self, '.button.action-primary.action-save', require_notification=False)

    def click_image_plugin(self):
        """
        Clicks image plugin icon from toolbar.
        """
        self.q(css='.mce-i-image').click()

    def click_url_plugin(self):
        """
        Clicks URL icon from toolbar.
        """
        self.q(css='.mce-i-link').click()

    def insert_link(self, link_to_insert):
        """
        Inserts link in image plugin and URL setting form.
        """
        set_input_value(self, '[class="mce-textbox mce-placeholder"]', link_to_insert)
        self.q(css='.mce-widget.mce-btn.mce-primary').click()

    def get_link_from_field(self):
        """
        Gets link from image plugin and URL setting form.
        """
        return get_input_value(self, '[class="mce-textbox mce-placeholder"]')

    def get_image_src(self):
        """
        Gets image source from tinyMCE editor.
        """
        self.browser.switch_to_frame(self.browser.find_element_by_css_selector('iframe'))
        src = self.q(css='.mce-content-body img').attrs('src')[0]
        self.browser.switch_to.default_content()
        return src

    def get_href(self):
        """
        Gets URL href from tinyMCE editor.
        """
        self.browser.switch_to_frame(self.browser.find_element_by_css_selector('iframe'))
        self.q(css='.mce-content-body a').first.click()
        href = self.q(css='.mce-content-body a').attrs('href')[0]
        self.browser.switch_to.default_content()
        return href

    def set_text(self, content):
        """
        Sets text in tinyMCE editor.
        """
        self.browser.execute_script("tinyMCE.activeEditor.setContent('%s')" % content)
        self.browser.switch_to_frame(self.browser.find_element_by_css_selector('iframe'))
        bc = self.q(css='.mce-content-body p').results[0]
        bc.send_keys(Keys.CONTROL, 'a')
        self.browser.switch_to.default_content()
        self.q(css='.mce-ico.mce-i-none').first.click()
        self.save()

    def open_code_editor(self):
        """
        Opens raw HTML code editor.
        """
        self.q(css=self.editor_mode_css).click()
        self.q(css='[aria-label="Edit HTML"]').click()

    def get_value_from_code_editor(self):
        """
        Gets value from raw HTML code editor
        """
        return get_codemirror_value(self)

    def set_input_in_raw_html_editor(self, content):
        """
        Sets and save input in raw HTML code editor.
        """
        self.wait_for_element_visibility('#modal-window-title', 'Wait for CodeMirror editor')
        type_in_codemirror(self, 0, content)
        self.save()

    def get_fonts_from_font_dropdown(self):
        self.q(css='[aria-label="Font Family"]').click()
        from nose.tools import set_trace;
        set_trace()
        fonts = self.q(css='.mce-menu').text[0]
        return [font.strip() for font in fonts.split('\n')]

    def actual_fonts(self):
        return list(self.CUSTOM_FONTS.keys()) + list(self.TINYMCE_FONTS.keys())

    def get_font_familt(self):
        self.q(css='[aria-label="Font Family"]').click()
        font_family = self.q(css='.mce-text').attrs('style')[0].replace('font-family: ', '')






    def get_dropdowns_length(self):
        return len(self.q(css='.mce-listbox'))

    def get_dropdowns_names(self):
        return self.q(css='.mce-listbox span').text

    def get_toolbar_buttons_length(self):
        return len(self.q(css='.mce-widget[aria-label]'))

    def get_toolbar_buttons_names(self):
        return self.q(css='.mce-widget[aria-label]').attrs('aria-label')












