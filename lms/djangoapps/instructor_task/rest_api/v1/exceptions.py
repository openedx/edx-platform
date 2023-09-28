"""
Exception classes for Instructor Task REST APIs.
"""


class TaskUpdateException(Exception):
    """
    An exception that occurs when trying to update an instructor task instance. This covers scenarios where an updated
    task schedule is not valid, or we are trying to update a task that has already been processed (is no longer in the
    `SCHEDULED` state).
    """
    pass  # pylint: disable=unnecessary-pass
