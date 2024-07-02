"""
Enums for mobile_api users app.
"""
from enum import Enum


class EnrollmentStatuses(Enum):
    """
    Enum for enrollment statuses.
    """

    ALL = 'all'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    EXPIRED = 'expired'

    @classmethod
    def values(cls):
        """
        Returns string representation of all enum values.
        """
        return [e.value for e in cls]
