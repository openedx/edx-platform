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

    def get_field_val(self, field_display_name):
        """
        If editing, get the value of field

        Args:
            field_display_name(str): Name of the field for which the value is required
        Returns:
            (string): Value of the field
        """
        script = "return $('.wrapper-comp-setting label:contains({}) + input').val();".format(field_display_name)
        return self.browser.execute_script(script)

    def get_default_dropdown_value(self, css):
        """
        Gets default value from the dropdown
        Args:
            css(string): css of the dropdown for which default value is required
        Returns:
            value(string): Default dropdown value
        """
        element = self.browser.find_element_by_css_selector(css)
        dropdown_default_selection = Select(element)
        value = dropdown_default_selection.first_selected_option.text
        return value

    def select_from_dropdown(self, dropdown_name, value):
        """
        Selects from the dropdown
        Arguments:
            dropdown_name(string): Name of the dropdown to be opened
            value(string): Value to be selected
        """
        self.q(css='select[class="input setting-input"][name="{}"]'.format(dropdown_name)).first.click()
        self.wait_for_element_visibility('option[value="{}"]'.format(value), 'Dropdown is visible')
        self.q(css='option[value="{}"]'.format(value)).click()

    def get_value_from_the_dropdown(self, dropdown_name):
        """
        Get selected value from the dropdown
        Args:
            dropdown_name(string): Name of the dropdown
        Returns:
            (string): Selected Value from the dropdown

        """
        dropdown = self.browser.find_element_by_css_selector(
            'select[class="input setting-input"][name="{}"]'.format(dropdown_name)
        )
        return Select(dropdown).first_selected_option.text

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

    def revert_setting(self, display_name=False):
        """
        Click to revert setting to default
        """
        if display_name:
            self.q(css='.action.setting-clear.active').first.click()
        else:
            self.q(css='.action.setting-clear.active').results[1].click()

    def toggle_cheatsheet(self):
        """
        Toggle cheatsheet on toolbar
        """
        self.q(css='.cheatsheet-toggle').first.click()
        self.wait_for_element_visibility('.simple-editor-cheatsheet.shown', 'Cheatsheet is visible')

    def is_cheatsheet_present(self):
        """
        Check for cheatsheet presence
        Returns:
            bool: True if present
        """
        return self.q(css='.simple-editor-cheatsheet.shown').present

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
