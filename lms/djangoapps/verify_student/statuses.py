"""
Status enums for verify_student.
"""
from enum import StrEnum, auto


class VerificationAttemptStatus(StrEnum):
    """This class describes valid statuses for a verification attempt to be in."""

    # This is the initial state of a verification attempt, before a learner has started IDV.
    CREATED = auto()

    # A verification attempt is pending when it has been started but has not yet been completed.
    PENDING = auto()

    # A verification attempt is approved when it has been approved by some mechanism (e.g. automatic review, manual
    # review, etc).
    APPROVED = auto()

    # A verification attempt is denied when it has been denied by some mechanism (e.g. automatic review, manual review,
    # etc).
    DENIED = auto()
