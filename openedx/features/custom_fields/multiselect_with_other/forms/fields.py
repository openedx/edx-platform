from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectFormField

from openedx.features.custom_fields.multiselect_with_other.forms.widgets import (
    CheckboxSelectMultipleWithOther,
    RadioSelectWithOther
)
from openedx.features.custom_fields.multiselect_with_other.helpers import (
    add_other_field_in_choices,
    filter_other_field_checkbox_value,
    get_other_values
)


class MultiSelectWithOtherFormField(MultiSelectFormField):
    """
    Form field class to handle other text input field within the multiselect field
    """

    def __init__(self, other_max_length=None, *args, **kwargs):
        if kwargs.get('choices'):
            kwargs['choices'] = add_other_field_in_choices(kwargs['choices'])

        self.widget = RadioSelectWithOther if kwargs.get('max_choices') == 1 else CheckboxSelectMultipleWithOther

        super(MultiSelectWithOtherFormField, self).__init__(*args, **kwargs)

        self.other_max_length = other_max_length
        self.error_messages.update(
            dict(invalid_length=_(
                'Other field value, maximum allowed length violation. Allowed limit is upto {other_max_length}'
                ' characters.').format(
                other_max_length=other_max_length)))

    def valid_value(self, value):
        return len(value) <= self.other_max_length

    def validate(self, value):
        """
        Validate that the input is a list or tuple.
        """
        if self.required and not value:
            raise ValidationError(self.error_messages['required'], code='required')

        if self.other_max_length is not None:
            other_values = get_other_values(self.choices, value)
            for val in other_values:
                if not self.valid_value(val):
                    raise ValidationError(
                        self.error_messages['invalid_length'],
                        code='invalid_length',
                        params={'value': val},
                    )

    def to_python(self, value):
        """
        Returns a list of strings
        """
        return filter_other_field_checkbox_value(
            super(MultiSelectWithOtherFormField, self).to_python(value)
        )

    def clean(self, value):
        value = [val for val in value if val not in self.empty_values]
        return super(MultiSelectWithOtherFormField, self).clean(value)
