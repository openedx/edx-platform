"""
Utilities for string manipulation.
"""

import ast

def str_to_bool(str):
    """
    Converts "true" (case-insensitive) to the boolean True.
    Everything else will return False.
    """
    try:
        return ast.literal_eval(str.title())
    except:
        return False
