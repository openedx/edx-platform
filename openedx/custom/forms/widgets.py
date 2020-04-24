from django.forms.widgets import CheckboxSelectMultiple

from openedx.custom.helpers import get_other_values


class CheckboxSelectMultipleWithOther(CheckboxSelectMultiple):
    """
    Widget class to handle other value filed.
    """
    other_choice = None
    other_option_template_name = 'django/forms/widgets/text.html'

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super(CheckboxSelectMultipleWithOther, self).create_option(name, value, label, selected, index,
                                                                            subindex, attrs)

        if value == 'other':
            option.update({
                'value': self.other_choice,
                'type': 'text',
                'template_name': self.other_option_template_name,
                'is_other': True
            })

        return option

    def optgroups(self, name, value, attrs=None):
        """
        Return a list of optgroups for this widget.
        """

        other_values = get_other_values(self.choices, value)

        OTHER_CHOICE_INDEX = 0
        other_values = '' if not other_values else other_values.pop(OTHER_CHOICE_INDEX)

        self.other_choice = other_values

        return super(CheckboxSelectMultipleWithOther, self).optgroups(name, value, attrs)
