"""
Miscellaneous utility functions.
"""


def escape_invalid_characters(name, invalid_char_list, replace_with='_'):
    """
    Remove invalid characters from a variable and replace it with given character.
    Few chars are not allowed in asset displayname, during import/export
    Escape those chars with `replace_with` and return clean name

    Args:
        name (str): variable to escape chars from.
        invalid_char_list (list): Must be a list, and it should contain list of chars to be removed
            from name
        replace_with (str): Char used to replace invalid_char with.

    Returns:
        name (str): name without `invalid_char_list`.

    """

    for char in invalid_char_list:
        if char in name:
            name = name.replace(char, replace_with)
    return name
