"""
Enrollment track related signals.
"""


from django.dispatch import Signal

# The purely documentational providing_args argument for Signal is deprecated.
# So we are moving the args to a comment.

ENROLLMENT_TRACK_UPDATED = Signal()

UNENROLL_DONE = Signal()

ENROLL_STATUS_CHANGE = Signal()

REFUND_ORDER = Signal()

USER_EMAIL_CHANGED = Signal()
