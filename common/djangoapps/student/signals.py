"""
Signals emitted by the student Django application.
"""
from django.dispatch import Signal

UNENROLL_DONE = Signal(providing_args=["course_enrollment", "skip_refund"])
ENROLL_STATUS_CHANGE = Signal(providing_args=["event", "user", "course_id", "mode", "cost", "currency"])
REFUND_ORDER = Signal(providing_args=["course_enrollment"])
