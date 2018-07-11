"""
Miscellaneous utility functions.
"""
from functools import partial


def get_extended_due_date(node):
    """
    Gets the actual due date for the logged in student for this node, returning
    the extendeded due date if one has been granted and it is later than the
    global due date, otherwise returning the global due date for the unit.
    """
    if isinstance(node, dict):
        get = node.get
    else:
        get = partial(getattr, node)
    due_date = get('due', None)
    if not due_date:
        return due_date
    extended = get('extended_due', None)
    if not extended or extended < due_date:
        return due_date
    return extended
