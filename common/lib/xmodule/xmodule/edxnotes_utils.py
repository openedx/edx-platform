"""
Utilities related to edXNotes.
"""


import sys


def edxnotes(cls):
    """
    Conditional decorator that loads edxnotes only when they exist.
    """
    if "lms.djangoapps.edxnotes" in sys.modules:
        from lms.djangoapps.edxnotes.decorators import edxnotes as notes
        return notes(cls)
    else:
        return cls
