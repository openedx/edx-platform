"""
Utilities related to edXNotes.
"""
import sys


def edxnotes(cls):
    """
    Conditional decorator that loads edxnotes only when they exist.
    """
    if "edxnotes" in sys.modules:
        from edxnotes.decorators import edxnotes as notes  # pylint: disable=import-error
        return notes(cls)
    else:
        return cls
