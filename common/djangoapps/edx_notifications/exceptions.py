"""
Specialized exceptions for the Notification subsystem
"""


class ItemNotFoundError(Exception):
    """
    Generic exception when a look up fails. Since we are abstracting away the backends
    we need to catch any native exceptions and re-throw as a generic exception
    """


class ItemConflictError(Exception):
    """
    Generic exception when trying to save an object that has the same primary key
    """


class ChannelNotFound(Exception):
    """
    Exception when a channel could not be found
    """


class ItemIntegrityError(Exception):
    """
    Thrown when something to have an integrity error in our database
    """


class BulkOperationTooLarge(Exception):
    """
    Thrown when a bulk operation is determined to be too large
    """


class ChannelError(Exception):
    """
    Thrown when there has been a problem in the NotificationChannel
    """
