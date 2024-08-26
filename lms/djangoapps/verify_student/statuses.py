"""
Status enums for verify_student.
"""


class VerificationAttemptStatus:
    """This class describes valid statuses for a verification attempt to be in."""

    # This is the initial state of a verification attempt, before a learner has started IDV.
    created = "created"

    # A verification attempt is pending when it has been started but has not yet been completed.
    pending = "pending"

    # A verification attempt is approved when it has been approved by some mechanism (e.g. automatic review, manual
    # review, etc).
    approved = "approved"

    # A verification attempt is denied when it has been denied by some mechanism (e.g. automatic review, manual review,
    # etc).
    denied = "denied"
