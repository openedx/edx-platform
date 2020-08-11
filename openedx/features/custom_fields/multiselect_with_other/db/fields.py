"""This module contains django models for field class that support multi select"""

from django.core import exceptions, checks
from django.utils import six
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import capfirst
from multiselectfield import MultiSelectField
from multiselectfield.db.fields import MSFList
from multiselectfield.utils import string_type, get_max_length

from openedx.features.custom_fields.multiselect_with_other.forms.fields import MultiSelectWithOtherFormField
from openedx.features.custom_fields.multiselect_with_other.helpers import add_other_field_in_choices


@python_2_unicode_compatible
class OtherMultiSelectFieldList(MSFList):
    def __str__(self):
        selected_choice_list = [self.choices.get(int(i)) if i.isdigit() else (self.choices.get(i) or i) for i in self]
        return u', '.join([string_type(s) for s in selected_choice_list])


class MultiSelectWithOtherField(MultiSelectField):
    """This class is a Django Model field class that supports
        multi select along with other option
        The `other_max_length` parameter is required for this
        Choice keys can not contain commas and other field can not contain
        pipe character i.e. `|`
    """

    def __init__(self, other_max_length=None, *args, **kwargs):
        self.other_max_length = other_max_length
        self.other_delimiter = kwargs.get('other_delimiter', '|')

        if kwargs.get('max_length') is None and other_max_length is not None:
            choice_max_length = get_max_length(kwargs['choices'], kwargs.get('max_length'))
            kwargs['max_length'] = choice_max_length + other_max_length

        if kwargs.get('choices'):
            kwargs['choices'] = add_other_field_in_choices(kwargs['choices'])

        super(MultiSelectWithOtherField, self).__init__(*args, **kwargs)

        self.error_messages.update({
            'invalid_char': 'value %s contains invalid character `{other_delimiter}`'.format(
                other_delimiter=self.other_delimiter)
        })

    def get_prep_value(self, value):
        selected_value = other_value = ''
        choice_values = [choice[0] for choice in self.choices]
        if value:
            for val in value:
                if val in choice_values:
                    selected_value += val + ','
                else:
                    other_value = val

            selected_value += self.other_delimiter + other_value
        return selected_value

    def formfield(self, **kwargs):
        defaults = {
            'required': not self.blank,
            'label': capfirst(self.verbose_name),
            'help_text': self.help_text,
            'choices': self.choices,
            'max_length': self.max_length,
            'max_choices': self.max_choices,
            'other_max_length': self.other_max_length
        }
        if self.has_default():
            defaults['initial'] = self.get_default()
        defaults.update(kwargs)
        return MultiSelectWithOtherFormField(**defaults)

    def validate(self, value, model_instance):
        """ This function is to validate the input values for multi select field,
        however we are implementing field with support of other input filed
        we are disabling validations to let other input text(other option)
        pass to the database.

        :param value: list of all selected choice with other text.
        :param model_instance: current model instance for with it is saving data.
        :type value: list
        :type model_instance: MultiSelectWithOtherField
        """
        for opt_select in value:
            if self.other_delimiter in opt_select:
                raise exceptions.ValidationError(self.error_messages['invalid_char'] % value)

    def to_python(self, value):
        choices = dict(self.flatchoices)
        if value:
            if isinstance(value, list):
                return value
            elif isinstance(value, string_type):
                choices_before_and_after_delimiter = value.split(self.other_delimiter)
                selected_choices = [choice for choice in choices_before_and_after_delimiter[0].split(',')
                                    if choice.strip()]
                if len(choices_before_and_after_delimiter) > 1 and choices_before_and_after_delimiter[1].strip():
                    selected_choices.append(choices_before_and_after_delimiter[1])
                return OtherMultiSelectFieldList(choices, selected_choices)
            elif isinstance(value, (set, dict)):
                return MSFList(choices, list(value))
        return MSFList(choices, [])

    def _check_other_max_length_attribute(self, **kwargs):
        """ This function is to validate the MultiSelectWithOtherField has a
        'other_max_length' attribute.
        :param **kwargs: arguments
        :type **kwargs: dictionary
         """
        if self.other_max_length is None:
            return [
                checks.Error(
                    "MultiSelectWithOtherField must define a 'other_max_length' attribute.",
                    obj=self,
                    id='fields.E120',
                )
            ]
        elif not isinstance(self.other_max_length, six.integer_types) or self.other_max_length <= 0:
            return [
                checks.Error(
                    "'other_max_length' must be a positive integer.",
                    obj=self,
                    id='fields.E121',
                )
            ]
        else:
            return []

    def check(self, **kwargs):
        errors = super(MultiSelectWithOtherField, self).check(**kwargs)
        errors.extend(self._check_other_max_length_attribute(**kwargs))
        return errors
