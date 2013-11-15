"""
Utilities for string manipulation.
"""

def str_to_bool(str):
    """
    Converts "true" (case-insensitive) to the boolean True.
    Everything else will return False (including None).

    An error will be thrown for non-string input (besides None).
    """
    return False if str is None else str.lower() == "true"
