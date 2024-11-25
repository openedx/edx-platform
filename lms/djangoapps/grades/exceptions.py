"""
Custom exceptions raised by grades.
"""


<<<<<<< HEAD
class DatabaseNotReadyError(IOError):
    """
    Subclass of IOError to indicate the database has not yet committed
    the data we're trying to find.
=======
class ScoreNotFoundError(IOError):
    """
    Subclass of IOError to indicate the staff has not yet graded the problem or
    the database has not yet committed the data we're trying to find.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass
