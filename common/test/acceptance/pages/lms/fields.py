# -*- coding: utf-8 -*-
"""
Mixins for fields.
"""
from bok_choy.promise import EmptyPromise

from common.test.acceptance.tests.helpers import get_selected_option_text, select_option_by_text


class FieldsMixin(object):
    """
    Methods for testing fields in pages.
    """

    def field(self, field_id):
        """
        Return field with field_id.
        """
        query = self.q(css='.u-field-{}'.format(field_id))
        return query.text[0] if query.present else None

    def wait_for_field(self, field_id):
        """
        Wait for a field to appear in DOM.
        """
        EmptyPromise(
            lambda: self.field(field_id) is not None,
            "Field with id \"{0}\" is in DOM.".format(field_id)
        ).fulfill()

    def mode_for_field(self, field_id):
        """
        Extract current field mode.

        Returns:
            `placeholder`/`edit`/`display`
        """
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-{}'.format(field_id))

        if not query.present:
            return None

        field_classes = query.attrs('class')[0].split()

        if 'mode-placeholder' in field_classes:
            return 'placeholder'

        if 'mode-display' in field_classes:
            return 'display'

        if 'mode-edit' in field_classes:
            return 'edit'

    def icon_for_field(self, field_id, icon_id):
        """
        Check if field icon is present.
        """
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-{} .u-field-icon'.format(field_id))
        return query.present and icon_id in query.attrs('class')[0].split()

    def title_for_field(self, field_id):
        """
        Return the title of a field.
        """
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-{} .u-field-title'.format(field_id))
        return query.text[0] if query.present else None

    def message_for_field(self, field_id):
        """
        Return the current message in a field.
        """
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-{} .u-field-message'.format(field_id))
        return query.text[0] if query.present else None

    def message_for_textarea_field(self, field_id):
        """
        Return the current message for textarea field.
        """
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-{} .u-field-message-help'.format(field_id))
        return query.text[0] if query.present else None

    def wait_for_message(self, field_id, message):
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
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-{} .u-field-message .fa'.format(field_id))
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

    def make_field_editable(self, field_id):
        """
        Make a field editable.
        """
        query = self.q(css='.u-field-{}'.format(field_id))

        if not query.present:
            return None

        field_classes = query.attrs('class')[0].split()

        if 'mode-placeholder' in field_classes or 'mode-display' in field_classes:
            if field_id == 'bio':
                bio_field_selector = '.u-field-bio > .wrapper-u-field'
                self.wait_for_element_visibility(bio_field_selector, 'Bio field is visible')
                self.browser.execute_script("$('" + bio_field_selector + "').click();")
            else:
                self.q(css='.u-field-{}'.format(field_id)).first.click()

    def value_for_readonly_field(self, field_id):
        """
        Return the value in a readonly field.
        """
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-{} .u-field-value'.format(field_id))
        if not query.present:
            return None

        return query.text[0]

    def value_for_text_field(self, field_id, value=None, press_enter=True):
        """
        Get or set the value of a text field.
        """
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-{} input'.format(field_id))
        if not query.present:
            return None

        if value is not None:
            current_value = query.attrs('value')[0]
            query.results[0].send_keys(u'\ue003' * len(current_value))  # Delete existing value.
            query.results[0].send_keys(value)  # Input new value
            if press_enter:
                query.results[0].send_keys(u'\ue007')  # Press Enter
        return query.attrs('value')[0]

    def set_value_for_textarea_field(self, field_id, value):
        """
        Set the value of a textarea field.
        """
        self.wait_for_field(field_id)
        self.make_field_editable(field_id)

        field_selector = '.u-field-{} textarea'.format(field_id)
        self.wait_for_element_presence(field_selector, 'Editable textarea is present.')

        query = self.q(css=field_selector)
        query.fill(value)
        query.results[0].send_keys(u'\ue007')  # Press Enter

    def get_non_editable_mode_value(self, field_id):
        """
        Return value of field in `display` or `placeholder` mode.
        """
        self.wait_for_field(field_id)
        self.wait_for_ajax()

        return self.q(css='.u-field-{} .u-field-value .u-field-value-readonly'.format(field_id)).text[0]

    def value_for_dropdown_field(self, field_id, value=None):
        """
        Get or set the value in a dropdown field.
        """
        self.wait_for_field(field_id)

        self.make_field_editable(field_id)

        query = self.q(css='.u-field-{} select'.format(field_id))
        if not query.present:
            return None

        if value is not None:
            select_option_by_text(query, value)

        if self.mode_for_field(field_id) == 'edit':
            return get_selected_option_text(query)
        else:
            return self.get_non_editable_mode_value(field_id)

    def link_title_for_link_field(self, field_id):
        """
        Return the title of the link in a link field.
        """
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-link-title-{}'.format(field_id))
        return query.text[0] if query.present else None

    def wait_for_link_title_for_link_field(self, field_id, expected_title):
        """
        Wait until the title of the specified link field equals expected_title.
        """
        return EmptyPromise(
            lambda: self.link_title_for_link_field(field_id) == expected_title,
            "Link field with link title \"{0}\" is visible.".format(expected_title)
        ).fulfill()

    def click_on_link_in_link_field(self, field_id, field_type='a'):
        """
        Click the link in a link field.
        """
        self.wait_for_field(field_id)

        query = self.q(css='.u-field-{} {}'.format(field_id, field_type))
        if query.present:
            query.first.click()

    def error_for_field(self, field_id):
        """
        Returns bool based on the highlighted border for field.
        """
        query = self.q(css='.u-field-{}.error'.format(field_id))
        return True if query.present else False
