"""
Base class for account settings page.
"""
from . import BASE_URL
from bok_choy.page_object import PageObject


READONLY_FIELD_SELECTOR = '.account-settings-field.{} .account-settings-field-value'
TEXT_FIELD_SELECTOR = '.account-settings-field.{} .account-settings-field-value > input'
DROPDOWN_FIELD_SELECTOR = '.account-settings-field.{} .account-settings-field-value option'
LINK_FIELD_SELECTOR = '.account-settings-field.{} .account-settings-field-value > a'

SETTING_FIELDS = {
    'readonly': ['username'],
    'text': ['name', 'email'],
    'dropdown': ['language', 'education', 'gender', 'birth_year', 'country', 'timezone', 'preferred_langauge'],
    'link': ['password', 'facebook', 'google']
}

class AccountSettingsPage(PageObject):
    """
    Tests for Account Settings Page.
    """

    url = "{base}/{settings}".format(base=BASE_URL, settings='account/settings')

    def is_browser_on_page(self):
        return 'Account Settings' in self.browser.title

    def _field_type(self, name):
        """
        Returns type of a field.

        Arguments:
            name (str): field name

        Returns:
            field type
        """
        for field_type, fields in SETTING_FIELDS.items():
            if name in fields:
                return field_type

    def get_field_value(self, name):
        """
        Returns value of a field

        Arguments:
            name (str): field name

        Returns:
            field value
        """
        field_type = self._field_type(name)

        if field_type == 'readonly':
            return self.q(css=READONLY_FIELD_SELECTOR.format(name)).text[0]
        elif field_type == 'text':
            return self.q(css=TEXT_FIELD_SELECTOR.format(name)).attrs('value')[0]
        elif field_type == 'dropdown':
            return self.q(css=DROPDOWN_FIELD_SELECTOR.format(name)).filter(lambda el: el.is_selected()).first.text[0]
        elif field_type == 'link':
            return self.q(css=LINK_FIELD_SELECTOR.format(name)).attrs('href')[0]

    def set_field_value(self, name, value):
        """
        Set value of a field

        Arguments:
            name (str): field name
            value (str): field value
        """
        raise NotImplementedError()
        # TODO! Functionality will be added once fields values can be saved.

    @property
    def sections(self):
        """
        Returns list of section names.
        """
        return self.q(css='.account-settings-section-header').text
