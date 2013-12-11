"""
Miscellaneous utility functions.
"""


def get_extended_due_date(node):
    """
    Gets the actual due date for the logged in student for this node, returning
    the extendeded due date if one has been granted, otherwise returning the
    global due date for the unit.
    """
    due_date = getattr(node, 'extended_due', None)
    if not due_date:
        due_date = getattr(node, 'due', None)
    return due_date
