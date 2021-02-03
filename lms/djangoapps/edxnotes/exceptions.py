"""
Exceptions related to EdxNotes.
"""


class EdxNotesParseError(Exception):
    """
    An exception that is raised whenever we have issues with data parsing.
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


class EdxNotesServiceUnavailable(Exception):
    """
    An exception that is raised whenever EdxNotes service is unavailable.
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass
