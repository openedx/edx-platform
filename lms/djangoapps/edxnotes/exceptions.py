"""
Exceptions related to EdxNotes.
"""


class EdxNotesParseError(Exception):
    """
    An exception that is raised whenever we have issues with data parsing.
    """
    pass


class EdxNotesServiceUnavailable(Exception):
    """
    An exception that is raised whenever EdxNotes service is unavailable.
    """
    pass
