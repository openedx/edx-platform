"""This module implements the Radio and Checkbox widgets for MultiSelectWithOther field"""
from django.forms.widgets import CheckboxSelectMultiple

from openedx.features.custom_fields.multiselect_with_other.helpers import (
    filter_other_field_checkbox_value,
    get_other_values
)


class CheckboxSelectMultipleWithOther(CheckboxSelectMultiple):
    """ Implements checkbox widget for MultiSelectWithOther field"""
    other_choice = None
    other_option_template_name = 'other_field.html'

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super(CheckboxSelectMultipleWithOther, self).create_option(name, value, label, selected, index,
                                                                            subindex, attrs)

        if value == 'other':
            selected = False if self.other_choice == '' else True
            option.update({
                'value': self.other_choice,
                'selected': selected,
                'template_name': self.other_option_template_name,
                'is_other': True
            })

        return option

    def optgroups(self, name, value, attrs=None):
        """ Return a list of optgroups for this widget."""

        other_values = get_other_values(self.choices, value)

        OTHER_CHOICE_INDEX = 0
        other_values = '' if not other_values else other_values.pop(OTHER_CHOICE_INDEX)

        self.other_choice = other_values

        return super(CheckboxSelectMultipleWithOther, self).optgroups(name, value, attrs)

    def format_value(self, value):
        return super(CheckboxSelectMultipleWithOther, self).format_value(
            filter_other_field_checkbox_value(value)
        )


class RadioSelectWithOther(CheckboxSelectMultipleWithOther):
    """ Implements radio select widget for MultiSelectWithOther field"""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super(RadioSelectWithOther, self).create_option(name, value, label, selected, index, subindex, attrs)

        option.update({
            'type': 'radio'
        })

        if value != 'other':
            option['attrs']['onclick'] = "document.querySelector('.other_text[name={}]').disabled=true".format(name)

        return option
