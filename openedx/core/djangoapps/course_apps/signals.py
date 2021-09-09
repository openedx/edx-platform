"""
Signals for course apps.
"""
from django.dispatch import Signal

# A signal that's dispatched when the status for a course app that's available for a course
# isn't present in the `CourseAppStatus` table.
COURSE_APP_STATUS_INIT = Signal()
