def add_other_field_in_choices(choices):
    _choices = choices

    if isinstance(_choices, dict):
        _choices = _choices.items()

    if 'other' not in [c for c, _ in _choices]:
        if isinstance(choices, tuple):
            return choices + (('other', 'Other'),)
        if isinstance(choices, list):
            return choices + [('other', 'Other')]
        if isinstance(choices, dict):
            choices['other'] = 'Other'
            return choices

    return choices


def get_other_values(choices, value):
    """
    This function to separate other's value from list of choices
    :param choices: list of valid choices
    :param value: list of selected choices including other's value
    :return: list of other values.
    """
    choice_values = [choice[0] for choice in choices]
    other_values = [val for val in value if val not in choice_values]
    return other_values
