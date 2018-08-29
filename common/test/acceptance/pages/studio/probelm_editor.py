"""
Studio Problem Editor
"""
from common.test.acceptance.pages.studio.xblock_editor import XBlockEditorView
from common.test.acceptance.pages.common.utils import click_css
from selenium.webdriver.support.ui import Select


class ProblemXBlockEditorView(XBlockEditorView):
    """
    Represents the rendered view of an Problem editor.
    """

    editor_mode_css = '.edit-xblock-modal .editor-modes .editor-button'
    settings_mode = '.settings-button'
    settings_ordered = ["Blank Common Problem", "", "", "", "Never", "Finished", "False", "0"]

    def open_settings(self):
        """
        Clicks on the settings button
        """
        click_css(self, self.settings_mode)

    @property
    def setting_keys(self):
        """
        Returns the list of all the keys
        """
        all_keys = self.q(css='.label.setting-label').text
        # We do not require the key for 'Component Location ID'
        all_keys.pop()
        return all_keys

    def set_field_val(self, field_display_name, field_value):
        """
        If editing, set the value of a field.
        """
        selector = '.xblock-studio_view li.field label:contains("{}") + input'.format(field_display_name)
        script = "$(arguments[0]).val(arguments[1]).change();"
        self.browser.execute_script(script, selector, field_value)

    # def set_field_val(self, field_name, field_value, field_type='input'):
    #     """
    #     Set settings input `field` with `value`
    #
    #     Arguments:
    #         field_name (str): Name of field
    #         field_value (str): Name of value
    #         field_type (str): `input`, `select` etc(more to be added later)
    #
    #     """
    #     query = '.wrapper-comp-setting > label:nth-child(1)'
    #     field_id = ''
    #
    #     if field_type == 'input':
    #         for index, _ in enumerate(self.q(css=query)):
    #             if field_name in self.q(css=query).nth(index).text[0]:
    #                 field_id = self.q(css=query).nth(index).attrs('for')[0]
    #                 break
    #
    #         self.q(css='#{}'.format(field_id)).fill(field_value)
    #     elif field_type == 'select':
    #         self.q(css='select[name="{0}"] option[value="{1}"]'.format(field_name, field_value)).first.click()

    def get_field_val(self, field_display_name):
        """
        If editing, get the value of field
        Returns:
            (string): Value of the field
        """
        script = "return $('.wrapper-comp-setting label:contains({}) + input').val();".format(field_display_name)
        return self.browser.execute_script(script)

    @property
    def default_dropdown_values(self):
        """
        Gets default values from the dropdowns
        Returns:
            dropdown_values (list): A list of all the default dropdown values
        """
        dropdown_values = []
        elements = self.browser.find_elements_by_css_selector('select[class="input setting-input"][name]')
        for element in elements:
            dropdown_default_selection = Select(element)
            value = dropdown_default_selection.first_selected_option.text
            dropdown_values.append(value)
        return dropdown_values

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

    @property
    def default_field_values(self):
        """
        Gets default field values
        Returns:
            list: A list of all the default field values
        """
        return self.q(css='.input.setting-input[value]').attrs('value')

    @property
    def ordered_setting_values(self):
        """
        Arrange the setting values in exact order taken from the page
        Returns:
            ordered_values (list): A list of all the setting values in ordered form
        """
        unordered_values = self.default_field_values + self.default_dropdown_values
        ordered_values = sorted(unordered_values, key=lambda x: self.settings_ordered.index(x))
        return ordered_values

    @property
    def settings(self):
        """
        Place all the keys and values in tuples list
        Returns:
            list: A list of all the key and values in tuples
        """
        return zip(self.setting_keys, self.ordered_setting_values)

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

    def is_latex_comiler_present(self):
        """
        Checks for the presence of latex compiler settings presence
        Returns:
            bool: True if present
        """
        return self.q(css='.launch-latex-compiler').present

    def cancel(self):
        """
        Clicks cancel button
        """
        # self._click_button('.action-cancel')

        click_css(self, '.action-cancel')

    def save(self):
        """
        Clicks save button.
        """
        click_css(self, '.action-save')
