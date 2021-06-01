"""
Enrollment track related signals.
"""


from django.dispatch import Signal

ENROLLMENT_TRACK_UPDATED = Signal(providing_args=['user', 'course_key', 'mode', 'countdown'])
UNENROLL_DONE = Signal(providing_args=["course_enrollment", "skip_refund"])
ENROLL_STATUS_CHANGE = Signal(providing_args=["event", "user", "course_id", "mode", "cost", "currency"])
REFUND_ORDER = Signal(providing_args=["course_enrollment"])
SAILTHRU_AUDIT_PURCHASE = Signal(providing_args=["user", "course_id", "mode"])
