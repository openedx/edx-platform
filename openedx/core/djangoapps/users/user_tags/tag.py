"""
Abstract base class for all User Tags.
"""
from abc import abstractproperty


class UserTag(object):
    """
    Abstract base class for all User Tags.
    """
    # Optional type for grouping tags
    type = None

    @abstractproperty
    def name(self):
        """
        Platform's unique identifier for the tag.
        """
        raise NotImplementedError

    @abstractproperty
    def display_name(self):
        """
        Public display name for the tag.
        """
        raise NotImplementedError

    @abstractproperty
    def description(self):
        """
        Public description of the tag.
        """
        raise NotImplementedError
