"""
Enrollment track related signals.
"""


from django.dispatch import Signal

ENROLLMENT_TRACK_UPDATED = Signal()
UNENROLL_DONE = Signal()
ENROLL_STATUS_CHANGE = Signal()
REFUND_ORDER = Signal()
