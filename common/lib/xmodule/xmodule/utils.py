

def get_extended_due_date(node):
    due_date = getattr(node, 'extended_due', None)
    if not due_date:
        due_date = getattr(node, 'due', None)
    return due_date
