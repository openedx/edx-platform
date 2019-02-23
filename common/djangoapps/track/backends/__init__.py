"""
Event tracking backend module.

Contains the base class for event trackers, and implementation of some
backends.

"""



import abc


class BaseBackend(object, metaclass=abc.ABCMeta):
    """
    Abstract Base Class for event tracking backends.

    """

    def __init__(self, **kwargs):
        pass

    @abc.abstractmethod
    def send(self, event):
        """Send event to tracker."""
        pass
