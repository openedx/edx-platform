"""
Base class for badge backends.
"""
from abc import ABCMeta, abstractmethod


class BadgeBackend(object):
    """
    Defines the interface for badging backends.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def award(self, badge_class, user, evidence_url=None):
        """
        Create a badge assertion for the user using this backend.
        """
