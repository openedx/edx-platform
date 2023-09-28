"""
Enrollment track related signals.
"""


from django.dispatch import Signal

# The purely documentational providing_args argument for Signal is deprecated.
# So we are moving the args to a comment.

# providing_args=['user', 'course_key', 'mode', 'countdown']
ENROLLMENT_TRACK_UPDATED = Signal()

# providing_args=["course_enrollment", "skip_refund"]
UNENROLL_DONE = Signal()

# providing_args=["event", "user", "course_id", "mode", "cost", "currency"]
ENROLL_STATUS_CHANGE = Signal()

# providing_args=["course_enrollment"]
REFUND_ORDER = Signal()

USER_EMAIL_CHANGED = Signal()
