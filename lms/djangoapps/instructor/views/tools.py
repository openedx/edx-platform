"""
Tools for the instructor dashboard
"""
def strip_if_string(value):
    if isinstance(value, basestring):
        return value.strip()
    return value
