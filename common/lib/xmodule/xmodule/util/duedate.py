"""
Miscellaneous utility functions.
"""


def get_extended_due_date(node):
    """
    Gets the actual due date for the logged in student for this node, returning
    the extendeded due date if one has been granted and it is later than the
    global due date, otherwise returning the global due date for the unit.
    """
    due_date = getattr(node, 'due', None)
    if not due_date:
        return due_date
    extended = getattr(node, 'extended_due', None)
    if not extended or extended < due_date:
        return due_date
    return extended
