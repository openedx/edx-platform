"""
User Tag Contexts.
"""
from abc import abstractproperty


class UserTagContext(object):
    """
    Abstract base class for all User Tag Contexts.
    A user tag context provides the scope in which a User Tag
    is applied.
    """
    @abstractproperty
    def id(self):  # pylint: disable=invalid-name
        """
        Returns the unique identifier for this context.
        """
        raise NotImplementedError
