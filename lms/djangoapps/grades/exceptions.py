"""
Custom exceptions raised by grades.
"""


class ScoreNotFoundError(IOError):
    """
    Subclass of IOError to indicate the staff has not yet graded the problem or
    the database has not yet committed the data we're trying to find.
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass
