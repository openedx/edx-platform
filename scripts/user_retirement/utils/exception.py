"""
Exceptions used by various utilities.
"""


class BackendError(Exception):
    pass


class HttpDoesNotExistException(Exception):
    """
    Called when the server sends a 404 error.
    """
    pass
