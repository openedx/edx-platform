"""
Base class for account settings page.
"""
from common.test.acceptance.pages.lms import BASE_URL

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise

from common.test.acceptance.pages.lms.fields import FieldsMixin


class AccountSettingsPage(FieldsMixin, PageObject):
    """
    Tests for Account Settings Page.
    """

    url = "{base}/{settings}".format(base=BASE_URL, settings='account/settings')

    def is_browser_on_page(self):
        return self.q(css='.account-settings-container').present

    def sections_structure(self):
        """
        Return list of section titles and field titles for each section.

        Example: [
            {
                'title': 'Section Title'
                'fields': ['Field 1 title', 'Field 2 title',...]
            },
            ...
        ]
        """
        structure = []

        sections = self.q(css='.section')
        for section in sections:
            section_title_element = section.find_element_by_class_name('section-header')
            field_title_elements = section.find_elements_by_class_name('u-field-title')

            structure.append({
                'title': section_title_element.text,
                'fields': [element.text for element in field_title_elements],
            })

        return structure

    def _is_loading_in_progress(self):
        """
        Check if loading indicator is visible.
        """
        query = self.q(css='.ui-loading-indicator')
        return query.present and 'is-hidden' not in query.attrs('class')[0].split()

    def wait_for_loading_indicator(self):
        """
        Wait for loading indicator to become visible.
        """
        EmptyPromise(self._is_loading_in_progress, "Loading is in progress.").fulfill()

    def switch_account_settings_tabs(self, tab_id):
        """
        Switch between the different account settings tabs.
        """
        self.q(css='#{}'.format(tab_id)).click()

    @property
    def is_order_history_tab_visible(self):
        """ Check if tab with the name "Order History" is visible."""
        return self.q(css='.u-field-orderHistory').visible

    def get_value_of_order_history_row_item(self, field_id, field_name):
        """ Return the text value of the provided order field name."""
        query = self.q(css='.u-field-{} .u-field-order-{}'.format(field_id, field_name))
        return query.text[0] if query.present else None

    def order_button_is_visible(self, field_id):
        """ Check that if hovering over the order history row shows the
        order detail link or not.
        """
        return self.q(css='.u-field-{} .u-field-{}'.format(field_id, 'link')).visible
