"""
The `compat` module provides support for backwards compatibility with older
versions of django/python, and compatibility wrappers around optional packages.
"""


# handle different QuerySet representations
def queryset_to_value_list(queryset):
    assert isinstance(queryset, str)

    # django 1.10 introduces syntax "<QuerySet [(#1), (#2), ...]>"
    # we extract only the list of tuples from the string
    idx_bracket_open = queryset.find(u'[')
    idx_bracket_close = queryset.rfind(u']')

    return queryset[idx_bracket_open:idx_bracket_close + 1]
