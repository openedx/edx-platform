"""
Custom exceptions raised by grades.
"""


class DatabaseNotReadyError(IOError):
    """
    Subclass of IOError to indicate the database has not yet committed
    the data we're trying to find.
    """
    pass
