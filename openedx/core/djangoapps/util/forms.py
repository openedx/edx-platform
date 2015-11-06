"""
Custom forms-related types
"""

from django.core.exceptions import ValidationError
from django.forms import Field, MultipleHiddenInput


class MultiValueField(Field):
    """
    Field class that supports a set of values for a single form field.

    The field input can be specified as:
        1. a comma-separated-list (foo:bar1,bar2,bar3), or
        2. a repeated field in a MultiValueDict (foo:bar1, foo:bar2, foo:bar3)
        3. a combination of the above (foo:bar1,bar2, foo:bar3)

    Note that there is currently no way to pass a value that includes a comma.

    The resulting field value is a python set of the values as strings.
    """
    widget = MultipleHiddenInput

    def to_python(self, list_of_string_values):
        """
        Convert the form input to a list of strings
        """
        values = super(MultiValueField, self).to_python(list_of_string_values) or set()

        if values:
            # combine all values if there were multiple specified individually
            values = ','.join(values)

            # parse them into a set
            values = set(values.split(',')) if values else set()

        return values

    def validate(self, values):
        """
        Ensure no empty values were passed
        """
        if values and "" in values:
            raise ValidationError("This field cannot be empty.")
