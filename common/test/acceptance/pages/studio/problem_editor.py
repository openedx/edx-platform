"""
Studio Problem Editor
"""
from common.test.acceptance.pages.studio.xblock_editor import XBlockEditorView
from common.test.acceptance.pages.common.utils import click_css
from selenium.webdriver.support.ui import Select


class ProblemXBlockEditorView(XBlockEditorView):
    """
    Represents the rendered view of a Problem editor.
    """

    editor_mode_css = '.edit-xblock-modal .editor-modes .editor-button'
    settings_mode = '.settings-button'

    def open_settings(self):
        """
        Clicks on the settings button
        """
        click_css(self, self.settings_mode)

    def set_field_val(self, field_display_name, field_value):
        """
        If editing, set the value of a field.
        """
        selector = '.xblock-studio_view li.field label:contains("{}") + input'.format(field_display_name)
        script = "$(arguments[0]).val(arguments[1]).change();"
        self.browser.execute_script(script, selector, field_value)

    def get_default_dropdown_value(self, css):
        """
        Gets default value from the dropdown
        Arguments:
            css(string): css of the dropdown for which default value is required
        Returns:
            dropdown_value(string): Default dropdown value
        """
        element = self.browser.find_element_by_css_selector(css)
        dropdown_default_selection = Select(element)
        value = dropdown_default_selection.first_selected_option.text
        return value

    def get_settings(self):
        """
        Default settings of problem
        Returns:
            settings_dict(dictionary): A dictionary of all the default settings
        """
        settings_dict = {}
        number_of_settings = len(self.q(css='.wrapper-comp-setting'))
        css = '.list-input.settings-list .field.comp-setting-entry:nth-of-type({}) {}'

        for index in range(1, number_of_settings + 1):
            key = self.q(css=css.format(index, "label")).text[0]
            if self.q(css=css.format(index, "input")).present:
                value = self.q(css=css.format(index, "input")).attrs('value')[0]
            elif self.q(css=css.format(index, "select")).present:
                value = self.get_default_dropdown_value(css.format(index, "select"))
            settings_dict[key] = value

        return settings_dict

    def is_latex_compiler_present(self):
        """
        Checks for the presence of latex compiler settings
        Returns:
            bool: True if present
        """
        return self.q(css='.launch-latex-compiler').present

    def save(self):
        """
        Clicks save button.
        """
        click_css(self, '.action-save')
