"""
Event tracking backend module.

Contains the base class for event trackers, and implementation of some
backends.

"""

from __future__ import absolute_import

import abc


# pylint: disable=unused-argument
class BaseBackend(object):
    """
    Abstract Base Class for event tracking backends.

    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        pass

    @abc.abstractmethod
    def send(self, event):
        """Send event to tracker."""
        pass
