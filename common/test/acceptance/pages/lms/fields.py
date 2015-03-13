# -*- coding: utf-8 -*-
"""
Mixins for fields.
"""
from bok_choy.promise import EmptyPromise

from ...tests.helpers import get_selected_option_text, select_option_by_text


class FieldsMixin(object):
    """
    Methods for testing fields in pages.
    """
    def title_for_field(self, field_id):
        """
        Return the title of a field.
        """
        self.wait_for_ajax()

        query = self.q(css='.u-field-{} .u-field-title'.format(field_id))
        return query.text[0] if query.present else None

    def message_for_field(self, field_id):
        """
        Return the current message in a field.
        """
        self.wait_for_ajax()

        query = self.q(css='.u-field-{} .u-field-message'.format(field_id))
        return query.text[0] if query.present else None

    def wait_for_messsage(self, field_id, message):
        """
        Wait for a message to appear in a field.
        """
        EmptyPromise(
            lambda: message in (self.message_for_field(field_id) or ''),
            "Messsage \"{0}\" is visible.".format(message)
        ).fulfill()

    def indicator_for_field(self, field_id):
        """
        Return the name of the current indicator in a field.
        """
        self.wait_for_ajax()

        query = self.q(css='.u-field-{} .u-field-message i'.format(field_id))
        return [
            class_name for class_name
            in query.attrs('class')[0].split(' ')
            if class_name.startswith('message')
        ][0].partition('-')[2] if query.present else None

    def wait_for_indicator(self, field_id, indicator):
        """
        Wait for an indicator to appear in a field.
        """
        EmptyPromise(
            lambda: indicator == self.indicator_for_field(field_id),
            "Indicator \"{0}\" is visible.".format(self.indicator_for_field(field_id))
        ).fulfill()

    def value_for_readonly_field(self, field_id):
        """
        Return the value in a readonly field.
        """
        self.wait_for_ajax()

        return self.value_for_text_field(field_id)

    def value_for_text_field(self, field_id, value=None):
        """
        Get or set the value of a text field.
        """
        self.wait_for_ajax()

        query = self.q(css='.u-field-{} input'.format(field_id))
        if not query.present:
            return None

        if value is not None:
            current_value = query.attrs('value')[0]
            query.results[0].send_keys(u'\ue003' * len(current_value))  # Delete existing value.
            query.results[0].send_keys(value)  # Input new value
            query.results[0].send_keys(u'\ue007')  # Press Enter
        return query.attrs('value')[0]

    def value_for_dropdown_field(self, field_id, value=None):
        """
        Get or set the value in a dropdown field.
        """
        self.wait_for_ajax()

        query = self.q(css='.u-field-{} select'.format(field_id))
        if not query.present:
            return None

        if value is not None:
            select_option_by_text(query, value)
        return get_selected_option_text(query)

    def link_title_for_link_field(self, field_id):
        """
        Return the title of the link in a link field.
        """
        self.wait_for_ajax()

        query = self.q(css='.u-field-{} a'.format(field_id))
        return query.text[0] if query.present else None

    def click_on_link_in_link_field(self, field_id):
        """
        Click the link in a link field.
        """
        self.wait_for_ajax()

        query = self.q(css='.u-field-{} a'.format(field_id))
        if query.present:
            query.first.click()
