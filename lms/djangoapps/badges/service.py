"""
Badging service for XBlocks
"""
from badges.models import BadgeClass


class BadgingService(object):
    """
    A class that provides functions for managing badges which XBlocks can use.
    """
    get_badge_class = BadgeClass.get_badge_class
